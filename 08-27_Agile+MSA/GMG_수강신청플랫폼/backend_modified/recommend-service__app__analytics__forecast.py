import math
from datetime import datetime
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class DemandForecaster:
    """그룹·장비 분류별 주간 요청량을 시간순으로 학습하고 4주를 예측한다."""

    categorical_features = ["group_id", "category"]
    numeric_features = [
        "month",
        "week_of_year",
        "week_sin",
        "week_cos",
        "lag_1",
        "lag_2",
        "lag_4",
        "rolling_mean_4",
        "rolling_mean_8",
    ]
    feature_columns = categorical_features + numeric_features

    def __init__(self, horizon_weeks: int = 4, random_state: int = 42):
        self.horizon_weeks = horizon_weeks
        self.random_state = random_state

    def train_and_forecast(self, events: list[dict]) -> dict:
        weekly = self._weekly_demand(events)
        featured = self._add_features(weekly)
        unique_weeks = sorted(featured["week_start"].unique())
        if len(unique_weeks) < 28:
            raise ValueError("수요 예측에는 최소 28주의 이력이 필요합니다")

        test_week_count = min(12, max(4, len(unique_weeks) // 5))
        validation_week_count = min(8, max(4, len(unique_weeks) // 8))
        test_start = unique_weeks[-test_week_count]
        validation_start = unique_weeks[-(test_week_count + validation_week_count)]

        train = featured[featured["week_start"] < validation_start]
        validation = featured[
            (featured["week_start"] >= validation_start)
            & (featured["week_start"] < test_start)
        ]
        test = featured[featured["week_start"] >= test_start]
        if train.empty or validation.empty or test.empty:
            raise ValueError("학습·검증·테스트 기간을 나눌 수 있을 만큼 데이터가 충분하지 않습니다")

        candidate_factories = self._candidate_factories()
        candidate_metrics: dict[str, dict] = {}
        selected_name = None
        selected_wape = math.inf

        for name, factory in candidate_factories.items():
            try:
                model = factory()
                model.fit(train[self.feature_columns], train["demand"])
                prediction = np.clip(
                    model.predict(validation[self.feature_columns]), 0, None
                )
                metrics = self._metrics(validation["demand"].to_numpy(), prediction)
                candidate_metrics[name] = {"validation": metrics}
                if metrics["wape"] < selected_wape:
                    selected_wape = metrics["wape"]
                    selected_name = name
            except Exception as exc:
                candidate_metrics[name] = {"error": str(exc)}

        if selected_name is None:
            raise RuntimeError("학습 가능한 수요 예측 모델이 없습니다")

        development = featured[featured["week_start"] < test_start]
        selected_model = candidate_factories[selected_name]()
        selected_model.fit(development[self.feature_columns], development["demand"])
        test_prediction = np.clip(
            selected_model.predict(test[self.feature_columns]), 0, None
        )
        model_metrics = self._metrics(test["demand"].to_numpy(), test_prediction)
        baseline_prediction = np.clip(test["rolling_mean_4"].to_numpy(), 0, None)
        baseline_metrics = self._metrics(test["demand"].to_numpy(), baseline_prediction)
        candidate_metrics[selected_name]["test"] = model_metrics
        candidate_metrics["rolling_mean_4_baseline"] = {"test": baseline_metrics}

        final_model = candidate_factories[selected_name]()
        final_model.fit(featured[self.feature_columns], featured["demand"])
        forecasts = self._recursive_forecast(final_model, weekly)

        return {
            "trained_at": datetime.now(),
            "model_name": selected_name,
            "metrics": {
                "baseline_mae": baseline_metrics["mae"],
                "model_mae": model_metrics["mae"],
                "baseline_wape": baseline_metrics["wape"],
                "model_wape": model_metrics["wape"],
            },
            "candidate_metrics": candidate_metrics,
            "train_rows": int(len(development)),
            "test_rows": int(len(test)),
            "event_count": int(len(events)),
            "data_start": weekly["week_start"].min().date(),
            "data_end": weekly["week_start"].max().date(),
            "forecasts": forecasts,
        }

    def _weekly_demand(self, events: list[dict]) -> pd.DataFrame:
        if not events:
            raise ValueError("분석할 대여 요청 이력이 없습니다")
        frame = pd.DataFrame(events)
        required = {"event_time", "group_id", "category", "quantity", "loan_days"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"분석 데이터 필드가 부족합니다: {sorted(missing)}")

        frame["event_time"] = pd.to_datetime(frame["event_time"])
        frame["week_start"] = (
            frame["event_time"]
            .dt.to_period("W-SUN")
            .apply(lambda period: period.start_time)
        )
        frame["quantity"] = pd.to_numeric(frame["quantity"], errors="coerce").fillna(1)
        frame["loan_days"] = pd.to_numeric(frame["loan_days"], errors="coerce").fillna(7)

        aggregated = frame.groupby(
            ["week_start", "group_id", "category"], as_index=False
        ).agg(
            demand=("quantity", "sum"),
            average_loan_days=("loan_days", "mean"),
        )

        weeks = pd.date_range(
            aggregated["week_start"].min(),
            aggregated["week_start"].max(),
            freq="7D",
        )
        combinations = aggregated[["group_id", "category"]].drop_duplicates()
        full_index = pd.MultiIndex.from_product(
            [weeks, combinations.index], names=["week_start", "combo_index"]
        ).to_frame(index=False)
        full_index = full_index.merge(
            combinations.reset_index().rename(columns={"index": "combo_index"}),
            on="combo_index",
            how="left",
        ).drop(columns="combo_index")

        defaults = frame.groupby(["group_id", "category"], as_index=False)[
            "loan_days"
        ].mean().rename(columns={"loan_days": "default_loan_days"})
        weekly = full_index.merge(
            aggregated,
            on=["week_start", "group_id", "category"],
            how="left",
        ).merge(defaults, on=["group_id", "category"], how="left")
        weekly["demand"] = weekly["demand"].fillna(0.0)
        weekly["average_loan_days"] = weekly["average_loan_days"].fillna(
            weekly["default_loan_days"]
        ).fillna(7.0)
        return weekly.drop(columns="default_loan_days").sort_values(
            ["week_start", "group_id", "category"]
        ).reset_index(drop=True)

    def _add_features(self, weekly: pd.DataFrame) -> pd.DataFrame:
        frame = weekly.copy().sort_values(
            ["group_id", "category", "week_start"]
        )
        grouped = frame.groupby(["group_id", "category"], group_keys=False)["demand"]
        frame["lag_1"] = grouped.shift(1)
        frame["lag_2"] = grouped.shift(2)
        frame["lag_4"] = grouped.shift(4)
        frame["rolling_mean_4"] = grouped.transform(
            lambda values: values.shift(1).rolling(4).mean()
        )
        frame["rolling_mean_8"] = grouped.transform(
            lambda values: values.shift(1).rolling(8).mean()
        )
        frame = self._add_calendar_features(frame)
        return frame.dropna(subset=[
            "lag_1", "lag_2", "lag_4", "rolling_mean_4", "rolling_mean_8"
        ]).sort_values(["week_start", "group_id", "category"]).reset_index(drop=True)

    def _add_calendar_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        frame = frame.copy()
        week = frame["week_start"].dt.isocalendar().week.astype(int)
        frame["month"] = frame["week_start"].dt.month.astype(int)
        frame["week_of_year"] = week
        frame["week_sin"] = np.sin(2 * np.pi * week / 52.0)
        frame["week_cos"] = np.cos(2 * np.pi * week / 52.0)
        frame["group_id"] = frame["group_id"].astype(str)
        frame["category"] = frame["category"].astype(str)
        return frame

    def _candidate_factories(self) -> dict[str, Callable[[], Pipeline]]:
        def preprocessor(scale_numeric: bool = False):
            numeric_transformer = StandardScaler() if scale_numeric else "passthrough"
            return ColumnTransformer([
                (
                    "categorical",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    self.categorical_features,
                ),
                ("numeric", numeric_transformer, self.numeric_features),
            ])

        return {
            "poisson_regression": lambda: Pipeline([
                ("preprocess", preprocessor(scale_numeric=True)),
                ("model", PoissonRegressor(alpha=0.1, max_iter=1000)),
            ]),
            "random_forest": lambda: Pipeline([
                ("preprocess", preprocessor()),
                ("model", RandomForestRegressor(
                    n_estimators=220,
                    min_samples_leaf=2,
                    random_state=self.random_state,
                    n_jobs=-1,
                )),
            ]),
            "hist_gradient_boosting": lambda: Pipeline([
                ("preprocess", preprocessor()),
                ("model", HistGradientBoostingRegressor(
                    max_iter=220,
                    learning_rate=0.06,
                    max_leaf_nodes=15,
                    l2_regularization=0.2,
                    random_state=self.random_state,
                )),
            ]),
        }

    def _recursive_forecast(self, model: Pipeline, weekly: pd.DataFrame) -> list[dict]:
        histories: dict[tuple, list[float]] = {}
        loan_days: dict[tuple, float] = {}
        for (group_id, category), group in weekly.groupby(["group_id", "category"]):
            key = (group_id, category)
            ordered = group.sort_values("week_start")
            histories[key] = ordered["demand"].astype(float).tolist()
            loan_days[key] = float(ordered["average_loan_days"].mean())

        last_week = weekly["week_start"].max()
        results: list[dict] = []
        for step in range(1, self.horizon_weeks + 1):
            week_start = last_week + pd.Timedelta(weeks=step)
            rows = []
            keys = sorted(histories.keys(), key=lambda item: (str(item[0]), item[1]))
            for group_id, category in keys:
                history = histories[(group_id, category)]
                rows.append({
                    "group_id": str(group_id),
                    "category": str(category),
                    "week_start": week_start,
                    "lag_1": history[-1],
                    "lag_2": history[-2],
                    "lag_4": history[-4],
                    "rolling_mean_4": float(np.mean(history[-4:])),
                    "rolling_mean_8": float(np.mean(history[-8:])),
                })

            feature_frame = self._add_calendar_features(pd.DataFrame(rows))
            predictions = np.clip(
                model.predict(feature_frame[self.feature_columns]), 0, None
            )
            for key, prediction in zip(keys, predictions):
                histories[key].append(float(prediction))
                results.append({
                    "group_id": int(key[0]),
                    "category": str(key[1]),
                    "week_start": week_start.date(),
                    "predicted_demand": round(float(prediction), 4),
                    "average_loan_days": round(loan_days[key], 2),
                })
        return results

    def _metrics(self, actual: np.ndarray, predicted: np.ndarray) -> dict:
        denominator = max(float(np.abs(actual).sum()), 1.0)
        return {
            "mae": round(float(mean_absolute_error(actual, predicted)), 4),
            "rmse": round(float(math.sqrt(mean_squared_error(actual, predicted))), 4),
            "wape": round(float(np.abs(actual - predicted).sum() / denominator * 100), 4),
        }
