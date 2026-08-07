"""
================================================================================
프로그램명   : [심화 실습 1] 자료구조 집계 · 컴프리헨션 · 제너레이터
작성자       : 판교 7반 임유리
작성일       : 2026-08-06
설명         : Python_Practice1_Data.json(Sales, 100건)을 대상으로
               리스트/딕셔너리 컴프리헨션으로 조건 필터링·지역별 집계를 수행하고,
               Counter·defaultdict로 거래 건수·카테고리별 금액을 그룹화하며,
               제너레이터로 리스트 대비 메모리 사용량을 비교한다.
               마지막으로 월·카테고리 기준 매출을 집계해 상위 3개 조합을 추출한다.
================================================================================
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path # 파일 시스템의 경로를 문자열이 아닌 객체로 다룸
from pprint import pprint # 복잡한 자료형을 보기 쉽게 출력함


DATA_FILE = Path(__file__).with_name("Python_Practice1_Data.json") #json 파일을 읽어옴


def load_sales(file_path: Path) -> list[dict]:
    """JSON 파일에서 Sales 목록을 읽어 반환합니다."""
    with file_path.open("r", encoding="utf-8") as file: # 파일을 읽기 모드로 열기
        data = json.load(file) # json 데이터를 파이션 딕셔너리로 변환함

    return data["sales"]


def filter_high_value_sales(sales: list[dict]) -> list[dict]:
    """amount가 1000 이상인 거래를 반환합니다."""
    return [sale for sale in sales if sale["amount"] >= 1000]


def calculate_region_total(sales: list[dict]) -> dict[str, int]:
    """지역별 총매출을 딕셔너리 컴프리헨션으로 계산합니다."""
    regions = sorted({sale["region"] for sale in sales}) # sorted를 사용해 새로운 정렬된 리스트를 반환함

    return {
        region: sum( # 지역별 총 매출 계산
            sale["amount"]
            for sale in sales
            if sale["region"] == region
        )
        for region in regions
    }


def count_sales_by_region(sales: list[dict]) -> Counter:
    """Counter를 사용해 지역별 거래 건수를 계산합니다."""
    return Counter(sale["region"] for sale in sales)


def group_amounts_by_category(sales: list[dict]) -> dict[str, list[int]]:
    """defaultdict를 사용해 카테고리별 amount 목록을 만듭니다."""
    category_amounts = defaultdict(list) # defaultdict : 존재하지 않는 키에 접근할 때 기본값을 제공함

    for sale in sales: # 카테고리별 amount
        category_amounts[sale["category"]].append(sale["amount"])

    return dict(category_amounts)


def generate_high_value_sales(sales: list[dict]):
    """amount가 1000보다 큰 거래를 하나씩 생성합니다."""
    for sale in sales:
        if sale["amount"] > 1000:
            yield sale # yield : 함수가 호출될 때마다 값을 반환함


def calculate_monthly_category_total(
    sales: list[dict],
) -> dict[str, dict[str, int]]:
    """월과 카테고리를 기준으로 총매출을 계산합니다."""
    monthly_sales = defaultdict(lambda: defaultdict(int)) # lambda : 이름을 따로 쓰지 않고 한 줄로 간단히 만듦

    for sale in sales: # 월과 카테고리를 기준으로 총매출을 계산함
        month = sale["month"][:7]
        monthly_sales[month][sale["category"]] += sale["amount"]

    return {
        month: dict(category_totals)
        for month, category_totals in monthly_sales.items() # items : 딕셔너리에 있는 키와 값들의 쌍을 얻을 수 있음
    }


def get_top3_monthly_category(
    monthly_category_total: dict[str, dict[str, int]],
) -> list[tuple[str, str, int]]:
    """월과 카테고리 조합 중 매출 상위 3개를 반환합니다."""
    flattened = [
        (month, category, amount)
        for month, category_totals in monthly_category_total.items() # items : 딕셔너리에 있는 키와 값들의 쌍을 얻을 수 있음
        for category, amount in category_totals.items()
    ]

    return sorted(
        flattened,
        key=lambda item: item[2], # sorted 함수에서 특정 인덱스나 키를 기준으로 정렬할 때 사용함(amount를 기준으로 정렬함)
        reverse=True, # 내림차순 정렬
    )[:3]

# 결과 출력
def main() -> None:
    sales = load_sales(DATA_FILE)

    high_value_sales = filter_high_value_sales(sales)
    region_total = calculate_region_total(sales)
    region_count = count_sales_by_region(sales)
    category_amounts = group_amounts_by_category(sales)

    generator_result = generate_high_value_sales(sales)
    list_result = [sale for sale in sales if sale["amount"] > 1000] 
    generator_size = sys.getsizeof(generator_result)
    list_size = sys.getsizeof(list_result)

    monthly_category_total = calculate_monthly_category_total(sales)
    top3 = get_top3_monthly_category(monthly_category_total)

    print("1. 전체 거래 건수")
    print(len(sales))

    print("\n2. amount >= 1000인 거래 건수")
    print(len(high_value_sales))

    print("\n3. 지역별 총매출")
    pprint(region_total, sort_dicts=False)

    print("\n4. 지역별 거래 건수")
    pprint(region_count.most_common())

    print("\n5. 카테고리별 amount 목록")
    pprint(category_amounts, sort_dicts=False)

    print("\n6. 리스트와 제너레이터 메모리 비교")
    print(f"리스트 크기:{list_size} bytes")
    print(f"제너레이터 크기:{generator_size} bytes")
    print("제너레이터 객체가 더 작은가:", generator_size < list_size)

    print("\n7. 월별 카테고리 매출")
    pprint(monthly_category_total, sort_dicts=False)

    print("\n8. 월별 카테고리 매출 상위 3개")
    pprint(top3)


if __name__ == "__main__":
    main()


# 제공 받은 json 파일의 내용이 json이 아니라 오류를 일으켜서 json 형태로 바꿔주었다.
# 중첩 defaultdict를 사용하여 월별 카테고리 매출을 계산하는 부분에서 lambda 함수를 사용하여 기본값을 설정하는 부분이 좀 어려웠다.
# 키가 없으면 기본값 생성이 되는 defaultdict가 두번 중첩되어 있어서 좀 어려웠던 것 같다.
# sys.getsizeof()를 사용하여 제너레이터와 리스트의 메모리 크기를 비교할 수 있다는 것을 알게 되었다.
# 평소 메모리 크기를 비교해봐야겠다고 생각하지는 못했는데, 앞으로는 이 부분을 활용하면 좋을 것 같다고 생각이 들었다.
# 확실히 기본 개념들을 잘 숙지하고 있어야 코드를 이해하고 작성하는데 도움이 된다는 것을 느꼈다.
# 또한 스스로 미리 공부하고 복습하는 과정이 필요하다고 느꼈고, 특히 스스로 코드를 짜는 연습을 많이 해봐야겠다고 생각했다.

