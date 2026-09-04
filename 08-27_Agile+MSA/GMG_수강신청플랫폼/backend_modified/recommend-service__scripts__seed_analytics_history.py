import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analytics.repository import analytics_repository
from app.analytics.simulation import generate_simulation_events


def main():
    parser = argparse.ArgumentParser(
        description="GearHub Campus 분석용 18개월 시뮬레이션 이력을 생성합니다."
    )
    parser.add_argument("--groups", default="1,2,3,4,5,6,7,8")
    parser.add_argument("--weeks", type=int, default=78)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    group_ids = [int(value.strip()) for value in args.groups.split(",") if value.strip()]
    analytics_repository.ensure_schema()
    if args.reset:
        deleted = analytics_repository.clear_simulation_events()
        print(f"기존 시뮬레이션 이벤트 {deleted}건 삭제")

    events = generate_simulation_events(
        group_ids=group_ids,
        weeks=args.weeks,
        random_seed=args.seed,
    )
    inserted = analytics_repository.insert_events(events)
    print(f"분석용 대여 요청 이력 {inserted}건 적재 완료")


if __name__ == "__main__":
    main()
