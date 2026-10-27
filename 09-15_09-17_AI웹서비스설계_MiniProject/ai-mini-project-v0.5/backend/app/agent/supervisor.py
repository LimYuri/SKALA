"""
Supervisor
──────────────────────────────────────────────────────────────
작업자(worker) 노드 중 다음에 무엇을 실행할지 결정합니다.

작업자 목록
  researcher          질문에 필요한 근거 자료 수집 (문서 + 웹)
  competitor_analyst  분석 대상 기업별 현황 분석
  writer              보고서 작성
"""
from __future__ import annotations

from app.agent.state import AgentState
from app.agent.tracing import traced
from app.events import Route, emit

COMPARISON_HINTS = ("경쟁사", "기업별", "회사별", "기술 성숙도", "trl", "비교해", "비교 분석")
LATEST_HINTS = ("최근", "최신", "새로 발표", "이후", "출시", "샘플", "고객사 소식")


def _is_comparison(query: str, competitors: list[str]) -> bool:
    q = query.lower()
    named_competitors = sum(name.lower() in q for name in competitors)
    return named_competitors >= 2 or any(hint in q for hint in COMPARISON_HINTS)


def _needs_more_research(state: AgentState) -> bool:
    evidence = state.get("evidence", [])
    query = state.get("query", "").lower()
    latest_question = any(hint in query for hint in LATEST_HINTS)
    return len(evidence) < 2 or (latest_question and not any(e.get("kind") == "web" for e in evidence))


@traced("supervisor")
async def supervisor(state: AgentState) -> dict:
    plan = state.get("plan")
    index = state.get("plan_index", 0)
    previous_worker = state.get("next")
    reason = "작업 계획 완료"

    if not plan:
        compare = _is_comparison(state["query"], state.get("competitors", []))
        plan = ["researcher"] + (["competitor_analyst"] if compare else []) + ["writer"]
        reason = "질문 유형에 따라 근거 수집과 기업 비교 여부를 결정"
    elif previous_worker == "researcher" and state.get("research_attempts", 0) < 2 and _needs_more_research(state):
        plan = plan[:index] + ["researcher"] + plan[index:]
        reason = "검색 근거가 부족해 한 번 더 검색"
    elif index < len(plan):
        reason = "근거 수집 완료" if plan[index] == "writer" else "기업 비교 질문"

    next_worker = plan[index] if index < len(plan) else "writer"

    emit(Route(
        source="supervisor",
        target=next_worker,
        reason=reason,
    ))
    return {"plan": plan, "plan_index": index + 1, "next": next_worker}


def route_from_supervisor(state: AgentState) -> str:
    """조건부 엣지: Supervisor가 정한 다음 노드 이름을 돌려줍니다."""
    return state["next"]
