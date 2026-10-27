"""
작업자(worker) 노드와 평가 노드
──────────────────────────────────────────────────────────────
  researcher          근거 자료 수집
  competitor_analyst  분석 대상 기업별 현황 분석
  writer              보고서 작성 (답변 스트리밍)
  step_evaluator      작성된 보고서 평가
"""
from __future__ import annotations

import asyncio
import time

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.prompts import (
    COMPETITOR_ANALYST_SYSTEM,
    WRITER_SYSTEM,
    format_evidence,
    format_findings,
)
from app.agent.state import AgentState
from app.agent.tracing import traced
from app.events import BranchEnd, BranchStart, Evaluation, Progress, Token, emit
from app.llm import CostLimitReached, ainvoke_tracked, astream_tracked
from app.retrieval import index_exists, search_docs, search_web, web_search_enabled

COMPETITOR_TIMEOUT_SECONDS = 45


# ──────────────────────────────────────────────────────────────
# researcher : 근거 자료 수집
# ──────────────────────────────────────────────────────────────
@traced("researcher")
async def researcher(state: AgentState) -> dict:
    item_id, query = state["item_id"], state["query"]
    attempt = state.get("research_attempts", 0)
    search_query = query if attempt == 0 else f"{state['item_name']} {query} official source"

    if not index_exists(item_id):
        emit(Progress(node="researcher", message=f"'{item_id}' 문서 인덱스가 없습니다. scripts/ingest.py 를 먼저 실행하세요."))
    docs = await search_docs(item_id, search_query, k=4)
    emit(Progress(node="researcher", message=f"문서 검색 {len(docs)}건"))

    web = []
    if web_search_enabled():
        web_query = f"{state['item_name']} {query}"
        if attempt:
            web_query += " official announcement latest"
        web = await search_web(web_query, max_results=3)
        emit(Progress(node="researcher", message=f"웹 검색 {len(web)}건"))
    else:
        emit(Progress(node="researcher", message="TAVILY_API_KEY 가 없어 웹 검색을 건너뜁니다."))

    evidence = state.get("evidence", []) + docs + web
    unique = {(e.get("source"), e.get("title"), e.get("content")): e for e in evidence}
    return {"evidence": list(unique.values()), "research_attempts": attempt + 1}


# ──────────────────────────────────────────────────────────────
# competitor_analyst : 분석 대상 기업별 현황 분석
#  - 기업마다 근거를 추가로 찾고, LLM으로 현황과 TRL을 추정합니다.
#  - 기업 하나의 분석을 "갈래(branch)"라고 부르며, 갈래마다 시작/종료 이벤트를 남깁니다.
# ──────────────────────────────────────────────────────────────
async def analyze_competitor(state: AgentState, competitor: str) -> dict:
    """기업 하나를 분석하고 답변 검증용 근거 자료를 함께 돌려줍니다."""
    item_name = state["item_name"]
    search_query = f"{competitor} {item_name}"

    docs = await search_docs(state["item_id"], search_query, k=3)
    web = await search_web(search_query, max_results=2)
    evidence = docs + web

    messages = [
        SystemMessage(content=COMPETITOR_ANALYST_SYSTEM),
        HumanMessage(content=(
            f"분석 아이템: {item_name}\n분석 대상 기업: {competitor}\n\n"
            f"근거 자료:\n{format_evidence(evidence)}"
        )),
    ]
    analysis = await ainvoke_tracked(messages, node="competitor_analyst")
    return {
        "competitor": competitor,
        "analysis": analysis,
        "evidence": evidence,
    }


@traced("competitor_analyst")
async def competitor_analyst(state: AgentState) -> dict:
    competitors = state.get("competitors", [])
    emit(Progress(node="competitor_analyst", message=f"분석 대상 {len(competitors)}개 기업: {', '.join(competitors)}"))

    async def run_branch(competitor: str):
        emit(BranchStart(node="competitor_analyst", branch=competitor))
        started = time.perf_counter()
        try:
            return await asyncio.wait_for(
                analyze_competitor(state, competitor), timeout=COMPETITOR_TIMEOUT_SECONDS
            )
        except CostLimitReached as exc:
            emit(Progress(node="competitor_analyst", message=f"{competitor} 분석은 비용 상한으로 생략: {exc}"))
            return {"competitor": competitor, "analysis": "비용 상한으로 분석하지 못함.", "evidence": [], "available": False}
        except Exception as exc:  # noqa: BLE001
            emit(Progress(node="competitor_analyst", message=f"{competitor} 분석 실패: {type(exc).__name__}"))
            return {"competitor": competitor, "analysis": "분석 중 오류가 발생해 결과를 확보하지 못함.", "evidence": [], "available": False}
        finally:
            elapsed = int((time.perf_counter() - started) * 1000)
            emit(BranchEnd(node="competitor_analyst", branch=competitor, duration_ms=elapsed))

    findings = await asyncio.gather(*(run_branch(name) for name in competitors))
    return {"competitor_findings": findings}


# ──────────────────────────────────────────────────────────────
# writer : 보고서 작성 (작성 중인 내용을 Frontend로 스트리밍)
# ──────────────────────────────────────────────────────────────
POOR_OUTPUT_SAMPLE = (
    "## 1. 요약\n해당 기술은 업계에서 많은 관심을 받고 있으며 향후 성장이 기대됩니다. "
    "여러 기업이 개발을 진행하고 있고 시장 상황에 따라 경쟁이 치열해질 것으로 보입니다.\n\n"
    "## 2. 기술 개요\n이 기술은 성능과 효율을 높이기 위한 차세대 기술입니다. "
    "다양한 분야에서 활용될 수 있으며 중요성이 계속 커지고 있습니다.\n\n"
    "## 3. 경쟁사별 현황\n주요 기업들은 각자의 전략에 따라 기술 개발에 힘쓰고 있습니다. "
    "각 기업의 기술 수준은 상당히 높은 편으로 판단됩니다.\n\n"
    "## 4. 시사점\n지속적인 투자와 연구 개발이 필요합니다.\n\n"
    "## 5. 한계와 불확실성\n시장 상황은 변할 수 있습니다.\n"
)


@traced("writer")
async def writer(state: AgentState) -> dict:
    # 점검용 테스트 모드: 근거 없이 일반론만 담긴 "부실한 결과"를 만듭니다.
    if state.get("test_mode"):
        emit(Progress(node="writer", message="[테스트 모드] 부실한 중간 결과를 생성합니다."))
        emit(Token(node="writer", text=POOR_OUTPUT_SAMPLE))
        return {"draft": POOR_OUTPUT_SAMPLE}

    competitor_context = (
        f"분석 대상 기업: {', '.join(state.get('competitors', []))}\n\n"
        if state.get("competitor_findings") else ""
    )
    messages = [
        SystemMessage(content=WRITER_SYSTEM),
        HumanMessage(content=(
            f"사용자 질문: {state['query']}\n"
            f"분석 아이템: {state['item_name']}\n"
            f"{competitor_context}"
            f"근거 자료:\n{format_evidence(state.get('evidence', []))}\n\n"
            f"경쟁사 분석 결과:\n{format_findings(state.get('competitor_findings', []))}"
        )),
    ]
    draft = await astream_tracked(messages, node="writer")
    return {"draft": draft}


# ──────────────────────────────────────────────────────────────
# step_evaluator : 보고서 평가
#  - 통과하면 종료, 통과하지 못하면 writer 가 다시 작성합니다.
# ──────────────────────────────────────────────────────────────
MIN_REPORT_CHARS = 300


@traced("step_evaluator")
async def step_evaluator(state: AgentState) -> dict:
    draft = state.get("draft", "")
    attempt = state.get("eval_attempts", 0) + 1

    passed = len(draft.strip()) >= MIN_REPORT_CHARS
    reason = "보고서 분량 충족" if passed else f"보고서 분량 부족 ({len(draft.strip())}자)"

    emit(Evaluation(stage="report", passed=passed, reason=reason, attempt=attempt))
    return {"eval_passed": passed, "eval_reason": reason, "eval_attempts": attempt}


def route_after_evaluation(state: AgentState) -> str:
    return "end" if state.get("eval_passed") else "writer"
