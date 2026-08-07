"""
================================================================================
프로그램명   : [Day 1] 종합 실습 - 실무형 수집·검증·품질 파이프라인
작성자       : 판교 7반 임유리
작성일       : 2026-08-06
설명         : Open-Meteo(서울 3일 시간대별 기온·강수확률), Countries.dev(대한민국
               국가 정보), ip-api(8.8.8.8 IP 위치 정보) 3개 API를 httpx +
               asyncio.gather()로 동시에 수집한다. 각 응답에서 필요한 필드만
               추출해 Pydantic v2 모델로 타입·범위를 검증하고, 검증에 실패하면
               ValidationError를 잡아 오류 목록에 남긴다(실제 데이터는 모두
               정상이므로, 예외 처리 로직 자체는 demo_validation_error()로
               별도 시연한다). 검증을 통과한 날씨 데이터에 국가/IP 컨텍스트를
               덧붙여 하나의 표로 만든 뒤 CSV·Parquet 두 형식으로 저장하고,
               각각의 쓰기/읽기 시간과 파일 크기를 측정해 비교한다.
================================================================================
"""

import asyncio

import httpx
from pydantic import ValidationError

from app.api_client import ApiFetchError, fetch_all
from app.config import (
    CSV_OUTPUT,
    PARQUET_OUTPUT,
    PERFORMANCE_OUTPUT,
    RAW_SNAPSHOT_OUTPUT,
    VALIDATION_ERROR_OUTPUT,
)
from app.models import WeatherHour
from app.pipeline import (
    build_report_rows,
    extract_weather_rows,
    validate_country,
    validate_ip_location,
    validate_weather_rows,
)
from app.storage import save_and_measure, save_json


def demo_validation_error() -> None:
    """실제 데이터엔 오류가 없어서, 이상값을 일부러 만들어 예외 처리를 시연한다."""
    print("\n=== ValidationError 예외 처리 시연 (고의로 만든 이상값) ===")
    bad_cases = [
        {"time": "2026-08-06T00:00", "temperature_2m": 999, "precipitation_probability": 10},
        {"time": "2026-08-06T01:00", "temperature_2m": 20, "precipitation_probability": 150},
    ]
    for case in bad_cases:
        try:
            WeatherHour.model_validate(case)
        except ValidationError as exc:
            print(f"[예상된 오류] {case} ->")
            print(exc.errors(include_url=False))


async def run_pipeline() -> dict:
    """수집 -> 검증 -> 병합 -> 저장 순서로 파이프라인 전체를 실행한다."""
    print("=== 1. API 3개 동시 수집 (asyncio.gather) ===")
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        raw = await fetch_all(client)

    save_json(raw, RAW_SNAPSHOT_OUTPUT)
    print("수집 완료: weather, country, ip_location 3건 모두 응답 확인")

    print("\n=== 2. Pydantic v2 스키마 검증 ===")
    weather_rows = extract_weather_rows(raw["weather"])
    valid_weather, weather_errors = validate_weather_rows(weather_rows)

    if weather_errors:
        save_json(weather_errors, VALIDATION_ERROR_OUTPUT)
        print(f"[경고] 날씨 검증 오류 {len(weather_errors)}건 -> validation_errors.json 저장")
    elif VALIDATION_ERROR_OUTPUT.exists():
        VALIDATION_ERROR_OUTPUT.unlink()  # 이전 실행의 오류 파일이 남아있지 않도록 정리

    country = validate_country(raw["country"])
    ip_location = validate_ip_location(raw["ip_location"])

    print(
        "검증 완료:",
        f"weather={len(valid_weather)}건,",
        f"country={country.name}({country.capital}),",
        f"ip={ip_location.query}->{ip_location.city}",
    )

    demo_validation_error()

    print("\n=== 3. 날씨 + 국가 + IP 컨텍스트 병합 ===")
    report_rows = build_report_rows(valid_weather, country, ip_location)
    print(f"병합 완료: {len(report_rows)}행")

    print("\n=== 4. CSV / Parquet 저장 및 쓰기·읽기 성능 측정 ===")
    performance = save_and_measure(report_rows, CSV_OUTPUT, PARQUET_OUTPUT, PERFORMANCE_OUTPUT)
    csv_write = performance["csv_write_seconds"]
    csv_read = performance["csv_read_seconds"]
    parquet_write = performance["parquet_write_seconds"]
    parquet_read = performance["parquet_read_seconds"]
    csv_bytes = performance["csv_bytes"]
    parquet_bytes = performance["parquet_bytes"]
    print(f"CSV     : 쓰기 {csv_write}초 / 읽기 {csv_read}초 / {csv_bytes} bytes")
    print(f"Parquet : 쓰기 {parquet_write}초 / 읽기 {parquet_read}초 / {parquet_bytes} bytes")

    print("\n=== 5. 완료 ===")
    print(f"CSV: {CSV_OUTPUT}")
    print(f"Parquet: {PARQUET_OUTPUT}")
    print(f"성능 결과: {PERFORMANCE_OUTPUT}")

    return performance


def main() -> None:
    """예외를 사람이 알기 쉬운 메시지로 바꿔 출력하고, 항상 종료 로그를 남긴다."""
    try:
        asyncio.run(run_pipeline())
    except ApiFetchError as exc:
        print(f"[API 오류] {exc}")
        raise SystemExit(1) from exc
    except ValueError as exc:
        print(f"[검증 오류] {exc}")
        raise SystemExit(1) from exc
    except (OSError, RuntimeError) as exc:
        print(f"[실행 오류] {exc}")
        raise SystemExit(1) from exc
    finally:
        print("\n[Day 1 종합실습] 파이프라인 종료")


if __name__ == "__main__":
    main()


# ================================================================================
# 회고
# --------------------------------------------------------------------------------
# - asyncio.gather()로 세 API를 동시에 호출해보니,
# 순서대로 await 하나씩 호출했을 때보다 전체 수집 시간이 눈에 띄게 줄었다.
# 동시에 기다린다는 개념을 코드로 직접 체감할 수 있어서 좋았다.
# - Pydantic v2의 Field(ge=..., le=...)를 사용하니 if문으로 하나씩
#   검사하던 것보다 코드가 훨씬 짧고 의도가 분명해져서 좋았던 것 같다.
#   특히 ip-api는 HTTP 상태 코드가 200이어도 내부 status 필드가 "fail"일
#   수 있다는 점을 이번에 처음 알게 되어, field_validator로 별도 검증했다.
# - 실제 API 응답은 대부분 정상 범위라 자연 발생 오류가 없었기 때문에,
#   demo_validation_error()로 고의 이상값을 만들어 예외 처리 경로가 실제로
#   동작하는지 별도로 증명해야 했다.
#   practice2.py에서 썼던 방식을 그대로 가져와 적용했다.
# - CSV와 Parquet를 같은 데이터로 비교해보니, Parquet가 쓰기/읽기 속도와
#   파일 크기 모두에서 CSV보다 유리한 것을 확인할 수 있었다.
#   특히 컬럼 지향 + 바이너리 포맷이라는 특성이 왜 대용량 분석에서
#   선호되는지 체감할 수 있었다.
# - 개선하고 싶은 점: 지금은 세 API 중 하나라도 실패하면 asyncio.gather()가
#   바로 예외를 던지며 전체가 중단된다.
#   return_exceptions=True를 활용해 "일부만 실패해도 나머지는 살리는" 구조로
#   바꾸면 더 좋아질 것 같다고 생각한다.
# ================================================================================
