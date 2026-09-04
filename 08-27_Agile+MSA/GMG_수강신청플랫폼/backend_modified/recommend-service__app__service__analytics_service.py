import math
from collections import defaultdict

from app.analytics.forecast import DemandForecaster
from app.analytics.repository import analytics_repository
from app.client.course_client import course_client
from app.config.settings import settings
from app.model.analytics_schemas import (
    DemandForecastItem,
    EvaluationResponse,
    ForecastSummaryResponse,
    TrainResponse,
    TransferSuggestion,
    WeeklyForecast,
)


class DemandAnalyticsService:
    def __init__(self):
        self.repository = analytics_repository
        self.forecaster = DemandForecaster(settings.forecast_horizon_weeks)

    def initialize(self) -> None:
        self.repository.ensure_schema()

    def train(self) -> TrainResponse:
        events = self.repository.load_requested_events()
        result = self.forecaster.train_and_forecast(events)
        run_id = self.repository.save_forecast_run(result)
        return TrainResponse(
            runId=run_id,
            modelName=result["model_name"],
            eventCount=result["event_count"],
            modelWape=result["metrics"]["model_wape"],
            baselineWape=result["metrics"]["baseline_wape"],
            message="시간순 검증과 향후 4주 수요 예측을 완료했습니다.",
        )

    def evaluation(self) -> EvaluationResponse:
        run = self._latest_or_train()
        baseline_wape = float(run["baseline_wape"])
        model_wape = float(run["model_wape"])
        improvement = (
            (baseline_wape - model_wape) / baseline_wape * 100
            if baseline_wape > 0 else 0.0
        )
        return EvaluationResponse(
            runId=run["id"],
            trainedAt=run["trained_at"],
            modelName=run["model_name"],
            baselineMae=float(run["baseline_mae"]),
            modelMae=float(run["model_mae"]),
            baselineWape=baseline_wape,
            modelWape=model_wape,
            improvementPercent=round(improvement, 2),
            trainRows=run["train_rows"],
            testRows=run["test_rows"],
            eventCount=run["event_count"],
            dataStart=run["data_start"],
            dataEnd=run["data_end"],
            candidateMetrics=run["candidate_metrics"],
        )

    async def summary(self, group_id: int) -> ForecastSummaryResponse:
        run = self._latest_or_train()
        all_forecasts = self.repository.load_forecasts(run["id"])
        group_forecasts = [
            row for row in all_forecasts if int(row["group_id"]) == group_id
        ]
        assets = await course_client.get_analytics_assets()
        stock = self._stock_by_group_category(assets)
        required = self._required_units(all_forecasts)

        by_category: dict[str, list[dict]] = defaultdict(list)
        for row in group_forecasts:
            by_category[row["category"]].append(row)

        items: list[DemandForecastItem] = []
        for category, rows in sorted(by_category.items()):
            rows.sort(key=lambda item: item["week_start"])
            demand = sum(float(row["predicted_demand"]) for row in rows)
            average_days = sum(float(row["average_loan_days"]) for row in rows) / len(rows)
            required_units = required.get((group_id, category), 0)
            own = stock.get((group_id, category), {"total": 0, "available": 0})
            shared = stock.get((None, category), {"total": 0, "available": 0})
            shared_total = self._shared_allocation(
                group_id, category, shared["total"], required
            )
            shared_available = self._shared_allocation(
                group_id, category, shared["available"], required
            )
            total_stock = own["total"] + shared_total
            available_stock = own["available"] + shared_available
            shortage = max(0, required_units - total_stock)
            suggestions = self._transfer_suggestions(
                group_id,
                category,
                shortage,
                stock,
                required,
            )

            if shortage > 0:
                risk = "HIGH"
            elif required_units > 0 and total_stock > 0 and required_units / total_stock >= 0.8:
                risk = "MEDIUM"
            else:
                risk = "LOW"

            items.append(DemandForecastItem(
                groupId=group_id,
                category=category,
                forecastDemand=round(demand, 1),
                averageLoanDays=round(average_days, 1),
                requiredUnits=required_units,
                totalStock=total_stock,
                availableStock=available_stock,
                sharedStock=shared_total,
                shortageUnits=shortage,
                riskLevel=risk,
                weekly=[WeeklyForecast(
                    weekStart=row["week_start"],
                    predictedDemand=round(float(row["predicted_demand"]), 1),
                ) for row in rows],
                transferSuggestions=suggestions,
            ))

        return ForecastSummaryResponse(
            runId=run["id"],
            generatedAt=run["trained_at"],
            modelName=run["model_name"],
            horizonWeeks=settings.forecast_horizon_weeks,
            groupId=group_id,
            items=items,
        )

    def _latest_or_train(self) -> dict:
        run = self.repository.latest_run()
        if run is None:
            self.train()
            run = self.repository.latest_run()
        if run is None:
            raise RuntimeError("수요 예측 결과를 생성하지 못했습니다")
        return run

    def _stock_by_group_category(self, assets) -> dict[tuple, dict]:
        stock: dict[tuple, dict] = defaultdict(lambda: {"total": 0, "available": 0})
        for asset in assets:
            group_key = None if asset.visibility == "ORGANIZATION" else asset.ownerGroupId
            key = (group_key, asset.category.value)
            stock[key]["total"] += int(asset.totalQuantity or 0)
            stock[key]["available"] += int(asset.availableQuantity or 0)
        return dict(stock)

    def _required_units(self, forecasts: list[dict]) -> dict[tuple, int]:
        grouped: dict[tuple, list[dict]] = defaultdict(list)
        for row in forecasts:
            grouped[(int(row["group_id"]), row["category"])].append(row)

        required = {}
        for key, rows in grouped.items():
            peak_weekly_demand = max(float(row["predicted_demand"]) for row in rows)
            average_days = sum(float(row["average_loan_days"]) for row in rows) / len(rows)
            # 가장 수요가 높은 주의 동시 점유량에 15% 운영 여유를 더한다.
            required[key] = max(
                0,
                math.ceil(peak_weekly_demand * average_days / 7 * 1.15),
            )
        return required

    def _shared_allocation(
            self,
            target_group_id: int,
            category: str,
            shared_quantity: int,
            required: dict) -> int:
        """학교 공용 재고를 모든 그룹이 동시에 전량 보유한 것처럼 중복 계산하지 않는다."""
        if shared_quantity <= 0:
            return 0
        needs = {
            group_id: units
            for (group_id, item_category), units in required.items()
            if item_category == category and units > 0
        }
        target_need = needs.get(target_group_id, 0)
        total_need = sum(needs.values())
        if target_need <= 0 or total_need <= 0:
            return 0
        return min(
            target_need,
            max(0, math.floor(shared_quantity * target_need / total_need)),
        )

    def _transfer_suggestions(
            self,
            target_group_id: int,
            category: str,
            shortage: int,
            stock: dict,
            required: dict) -> list[TransferSuggestion]:
        if shortage <= 0:
            return []
        remaining = shortage
        suggestions = []
        candidate_group_ids = sorted({
            key[0] for key in stock.keys()
            if key[0] is not None and key[0] != target_group_id and key[1] == category
        })
        for group_id in candidate_group_ids:
            owned = stock.get((group_id, category), {"total": 0})["total"]
            need = required.get((group_id, category), 0)
            surplus = max(0, owned - need)
            if surplus <= 0:
                continue
            quantity = min(remaining, surplus)
            suggestions.append(TransferSuggestion(
                fromGroupId=group_id,
                category=category,
                suggestedQuantity=quantity,
            ))
            remaining -= quantity
            if remaining <= 0:
                break
        return suggestions


demand_analytics_service = DemandAnalyticsService()
