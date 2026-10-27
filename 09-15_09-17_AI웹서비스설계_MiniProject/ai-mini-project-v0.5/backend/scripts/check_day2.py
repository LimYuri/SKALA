"""빠른 로컬 점검: 라우팅, 병렬 경쟁사 분석, 비용 예약."""
from __future__ import annotations

import asyncio
import time

from langchain_core.messages import HumanMessage

from app.agent import nodes
from app.agent.supervisor import supervisor
from app.llm import CostLimitReached, RunCostBudget


async def main() -> None:
    q1 = {"query": "HBF는 HBM과 무엇이 다른가요?", "competitors": ["SK hynix", "SanDisk", "Samsung"]}
    first = await supervisor(q1)
    assert first["next"] == "researcher"
    q1.update(first, evidence=[{"kind": "doc"}, {"kind": "doc"}], research_attempts=1)
    assert (await supervisor(q1))["next"] == "writer"

    q2 = {"query": "SK hynix, SanDisk, Samsung의 HBF 현황과 TRL을 비교해 주세요.", "competitors": ["SK hynix", "SanDisk", "Samsung"]}
    q2.update(await supervisor(q2))
    assert q2["next"] == "researcher"
    q2.update(evidence=[{"kind": "doc"}, {"kind": "web"}], research_attempts=1)
    second = await supervisor(q2)
    assert second["next"] == "competitor_analyst"
    q2.update(second)
    assert (await supervisor(q2))["next"] == "writer"

    q3 = {"query": "최근 HBF 고객사 소식이 있나요?", "competitors": []}
    q3.update(await supervisor(q3))
    q3.update(evidence=[{"kind": "doc"}], research_attempts=1)
    retry = await supervisor(q3)
    assert retry["next"] == "researcher"
    q3.update(retry, evidence=[{"kind": "doc"}, {"kind": "web"}], research_attempts=2)
    assert (await supervisor(q3))["next"] == "writer"

    original = nodes.analyze_competitor

    async def fake_analysis(state, competitor):
        await asyncio.sleep(0.08)
        if competitor == "SanDisk":
            raise ValueError("simulated failure")
        return {"competitor": competitor, "analysis": "ok", "evidence": []}

    nodes.analyze_competitor = fake_analysis
    started = time.perf_counter()
    try:
        result = await nodes.competitor_analyst({"competitors": ["SK hynix", "SanDisk", "Samsung"]})
    finally:
        nodes.analyze_competitor = original
    assert [item["competitor"] for item in result["competitor_findings"]] == ["SK hynix", "SanDisk", "Samsung"]
    assert [item.get("available", True) for item in result["competitor_findings"]] == [True, False, True]
    assert time.perf_counter() - started < 0.15

    budget = RunCostBudget(0.01)
    reserve = await budget.reserve([HumanMessage(content="test")], "writer")
    await budget.settle(reserve, 0.0001)
    assert abs(budget.spent_usd - 0.0001) < 1e-9
    try:
        await RunCostBudget(0.000001).reserve([HumanMessage(content="test")], "writer")
    except CostLimitReached:
        pass
    else:
        raise AssertionError("low budget should reject a new LLM call")


if __name__ == "__main__":
    asyncio.run(main())
