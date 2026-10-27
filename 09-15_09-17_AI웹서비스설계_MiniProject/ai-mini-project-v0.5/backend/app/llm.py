"""
LLM / 임베딩 생성과 사용량 기록
- 모든 LLM 호출은 이 파일의 ainvoke_tracked / astream_tracked 를 거칩니다.
- 호출이 끝날 때마다 llm_usage 이벤트(토큰 수, 예상 비용)가 발생합니다.
"""
from __future__ import annotations

import asyncio
from contextvars import ContextVar, Token as ContextToken
from functools import lru_cache
from math import ceil

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import PRICING_PER_1M, settings
from app.events import LlmUsage, Progress, Token, emit


@lru_cache
def get_llm() -> ChatOpenAI:
    # stream_usage=True : 스트리밍 응답에서도 토큰 사용량을 받기 위한 옵션
    return ChatOpenAI(model=settings.llm_model, temperature=0, stream_usage=True)


@lru_cache
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=settings.embedding_model)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICING_PER_1M.get(model, (0.0, 0.0))
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


class CostLimitReached(RuntimeError):
    pass


class RunCostBudget:
    def __init__(self, limit_usd: float):
        self.limit_usd = limit_usd
        self.spent_usd = 0.0
        self.reserved_usd = 0.0
        self.lock = asyncio.Lock()

    async def reserve(self, messages: list[BaseMessage], node: str) -> float:
        model = settings.llm_model
        if model not in PRICING_PER_1M:
            raise CostLimitReached(f"{model} 단가표가 없어 비용 상한을 적용할 수 없습니다. PRICING_PER_1M을 확인하세요.")
        content = " ".join(str(message.content) for message in messages)
        # shortcut: mixed-script character estimate; provider usage settles actual cost.
        hangul = sum("가" <= char <= "힣" for char in content)
        non_ascii = sum(ord(char) > 127 and not ("가" <= char <= "힣") for char in content)
        input_tokens = ceil(hangul * 1.2 + non_ascii + (len(content) - hangul - non_ascii) / 3) + 16 * len(messages)
        max_output_tokens = 512 if node == "competitor_analyst" else 1100
        reserve = estimate_cost(model, input_tokens, max_output_tokens) * 1.15
        async with self.lock:
            if self.spent_usd + self.reserved_usd + reserve > self.limit_usd:
                raise CostLimitReached(
                    f"예상 누적 비용이 상한 ${self.limit_usd:.4f}를 넘을 수 있어 {node} LLM 호출을 건너뜁니다."
                )
            self.reserved_usd += reserve
        return reserve

    async def settle(self, reserve: float, actual: float) -> None:
        async with self.lock:
            self.reserved_usd -= reserve
            self.spent_usd += actual
            if self.spent_usd > self.limit_usd:
                emit(Progress(node="cost_guard", message=f"실제 비용 ${self.spent_usd:.4f}가 상한 ${self.limit_usd:.4f}를 초과했습니다. 이미 진행 중인 호출 비용 때문입니다."))

    async def release(self, reserve: float) -> None:
        async with self.lock:
            self.reserved_usd -= reserve


_run_budget: ContextVar[RunCostBudget | None] = ContextVar("run_cost_budget", default=None)


def set_run_budget(limit_usd: float) -> ContextToken:
    return _run_budget.set(RunCostBudget(limit_usd))


def reset_run_budget(token: ContextToken) -> None:
    _run_budget.reset(token)


def _usage_cost(message) -> tuple[int, int, float]:
    usage = getattr(message, "usage_metadata", None) or {}
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    return input_tokens, output_tokens, estimate_cost(settings.llm_model, input_tokens, output_tokens)


async def _emit_usage(node: str, message, reservation: float = 0.0) -> None:
    input_tokens, output_tokens, cost = _usage_cost(message)
    budget = _run_budget.get()
    if budget is not None:
        await budget.settle(reservation, cost)
    emit(LlmUsage(
        node=node,
        model=settings.llm_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
    ))


async def ainvoke_tracked(messages: list[BaseMessage], node: str) -> str:
    """LLM을 한 번 호출하고 응답 텍스트를 돌려줍니다. (사용량 이벤트 자동 발생)"""
    budget = _run_budget.get()
    reservation = await budget.reserve(messages, node) if budget is not None else 0.0
    try:
        response = await get_llm().bind(max_tokens=512 if node == "competitor_analyst" else 1100).ainvoke(messages)
        await _emit_usage(node, response, reservation)
        return response.content
    except BaseException:
        if budget is not None:
            await budget.release(reservation)
        raise


async def astream_tracked(messages: list[BaseMessage], node: str) -> str:
    """
    LLM 응답을 조각(token) 단위로 Frontend에 흘려보내면서 전체 텍스트를 돌려줍니다.
    조각들을 더해(+) 하나의 메시지로 합치면 마지막에 사용량 정보가 들어 있습니다.
    """
    budget = _run_budget.get()
    reservation = await budget.reserve(messages, node) if budget is not None else 0.0
    try:
        full = None
        async for chunk in get_llm().bind(max_tokens=1100).astream(messages):
            if chunk.content:
                emit(Token(node=node, text=chunk.content))
            full = chunk if full is None else full + chunk
        if full is None:
            if budget is not None:
                await budget.release(reservation)
            return ""
        await _emit_usage(node, full, reservation)
        return full.content
    except BaseException:
        if budget is not None:
            await budget.release(reservation)
        raise
