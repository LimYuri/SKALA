from datetime import date, datetime, time, timedelta
from uuid import NAMESPACE_URL, uuid5

import numpy as np


DEFAULT_CATEGORIES = [
    "COMPUTER",
    "DEVICE",
    "CAMERA_AUDIO",
    "PRESENTATION",
    "ELECTRONICS_IOT",
    "MAKER",
    "ACCESSORY",
]


def generate_simulation_events(
    group_ids: list[int],
    categories: list[str] | None = None,
    weeks: int = 78,
    end_date: date | None = None,
    random_seed: int = 42,
) -> list[dict]:
    """대학 학사 일정과 그룹별 차이를 포함한 재현 가능한 요청 이력을 만든다."""
    if not group_ids:
        raise ValueError("시뮬레이션에는 그룹 ID가 한 개 이상 필요합니다")
    categories = categories or DEFAULT_CATEGORIES
    rng = np.random.default_rng(random_seed)
    end_date = end_date or date.today()
    end_monday = end_date - timedelta(days=end_date.weekday())
    start_monday = end_monday - timedelta(weeks=weeks - 1)

    category_base = {
        "COMPUTER": 3.0,
        "DEVICE": 2.3,
        "CAMERA_AUDIO": 2.4,
        "PRESENTATION": 1.8,
        "ELECTRONICS_IOT": 1.9,
        "MAKER": 2.0,
        "ACCESSORY": 2.5,
    }
    category_loan_days = {
        "COMPUTER": 6,
        "DEVICE": 4,
        "CAMERA_AUDIO": 4,
        "PRESENTATION": 2,
        "ELECTRONICS_IOT": 8,
        "MAKER": 8,
        "ACCESSORY": 3,
    }

    events: list[dict] = []
    sequence = 1
    for week_index in range(weeks):
        week_start = start_monday + timedelta(weeks=week_index)
        for group_position, group_id in enumerate(group_ids):
            group_factor = 0.78 + (group_position % 5) * 0.11
            for category in categories:
                base = category_base.get(category, 2.0)
                season = _season_factor(week_start, category)
                trend = 1.0 + (week_index / max(weeks - 1, 1)) * 0.14
                interaction = _group_category_factor(group_position, category)
                expected = max(0.15, base * group_factor * season * trend * interaction)
                demand = int(rng.poisson(expected))

                for _ in range(demand):
                    day_offset = int(rng.integers(0, 5))
                    hour = int(rng.integers(9, 19))
                    minute = int(rng.integers(0, 60))
                    event_time = datetime.combine(
                        week_start + timedelta(days=day_offset),
                        time(hour=hour, minute=minute),
                    )
                    average_days = category_loan_days.get(category, 7)
                    loan_days = max(1, int(round(rng.normal(average_days, 1.5))))
                    event_id = str(uuid5(
                        NAMESPACE_URL,
                        f"gearhub-simulation-{random_seed}-{sequence}",
                    ))
                    events.append({
                        "event_id": event_id,
                        "event_time": event_time,
                        "event_type": "REQUESTED",
                        "request_id": 1_000_000 + sequence,
                        "user_id": group_id * 10_000 + int(rng.integers(1, 80)),
                        "group_id": group_id,
                        "asset_id": None,
                        "category": category,
                        "quantity": 1,
                        "loan_days": loan_days,
                    })
                    sequence += 1
    return events


def _season_factor(week_start: date, category: str) -> float:
    month = week_start.month
    day = week_start.day
    factor = 1.0

    # 방학에는 전반적인 수요가 줄고 학기 초에는 IT 장비가 증가한다.
    if month in {1, 2, 7, 8}:
        factor *= 0.58
    if month in {3, 9} and day <= 21 and category in {"COMPUTER", "DEVICE", "ACCESSORY"}:
        factor *= 1.65

    # 축제·학술제와 졸업작품 기간의 장비 수요를 반영한다.
    if month in {5, 10} and category in {"CAMERA_AUDIO", "PRESENTATION"}:
        factor *= 1.85
    if month in {6, 11, 12} and category in {"MAKER", "ELECTRONICS_IOT", "COMPUTER"}:
        factor *= 1.55
    if month in {4, 6, 10, 12} and category == "COMPUTER":
        factor *= 1.25
    return factor


def _group_category_factor(group_position: int, category: str) -> float:
    # 그룹마다 전공·활동 특성이 다르도록 고정된 상호작용을 준다.
    specialty = group_position % 4
    if specialty == 0 and category in {"MAKER", "ELECTRONICS_IOT"}:
        return 1.55
    if specialty == 1 and category in {"CAMERA_AUDIO", "PRESENTATION"}:
        return 1.55
    if specialty == 2 and category in {"COMPUTER", "DEVICE"}:
        return 1.45
    if specialty == 3 and category == "PRESENTATION":
        return 1.35
    return 0.92
