from datetime import date

from app.analytics.forecast import DemandForecaster
from app.analytics.simulation import DEFAULT_CATEGORIES, generate_simulation_events


def test_simulation_is_deterministic_and_large_enough_for_demo():
    first = generate_simulation_events(list(range(1, 9)), random_seed=17)
    second = generate_simulation_events(list(range(1, 9)), random_seed=17)

    assert len(first) == len(second)
    assert 8_000 <= len(first) <= 20_000
    assert first[:20] == second[:20]
    assert {event["category"] for event in first} == set(DEFAULT_CATEGORIES)


def test_time_ordered_training_produces_four_week_group_forecasts():
    events = generate_simulation_events(
        [11, 22, 33, 44],
        categories=["COMPUTER", "CAMERA_AUDIO", "MAKER"],
        weeks=60,
        end_date=date(2026, 8, 24),
        random_seed=42,
    )

    result = DemandForecaster(horizon_weeks=4).train_and_forecast(events)

    assert result["train_rows"] > result["test_rows"] > 0
    assert result["data_start"] < result["data_end"]
    assert len(result["forecasts"]) == 4 * 3 * 4
    assert result["metrics"]["model_wape"] >= 0
    assert result["metrics"]["baseline_wape"] >= 0
    assert result["model_name"] in {
        "poisson_regression",
        "random_forest",
        "hist_gradient_boosting",
    }
