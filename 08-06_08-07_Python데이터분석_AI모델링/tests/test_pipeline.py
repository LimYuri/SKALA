"""추출(extract) -> 검증(validate) -> 병합(build_report_rows) 로직 테스트."""

from app.models import CountryInfo, IpLocation
from app.pipeline import (
    build_report_rows,
    extract_country_fields,
    extract_ip_fields,
    extract_weather_rows,
    validate_weather_rows,
)


def test_extract_weather_rows_zips_three_arrays() -> None:
    """hourly의 세 배열을 시점별로 올바르게 묶는지 확인한다."""
    raw = {
        "hourly": {
            "time": ["2026-08-06T00:00", "2026-08-06T01:00"],
            "temperature_2m": [25.0, 24.5],
            "precipitation_probability": [10, 20],
        }
    }
    rows = extract_weather_rows(raw)
    assert rows == [
        {"time": "2026-08-06T00:00", "temperature_2m": 25.0, "precipitation_probability": 10},
        {"time": "2026-08-06T01:00", "temperature_2m": 24.5, "precipitation_probability": 20},
    ]


def test_extract_country_fields_picks_needed_keys() -> None:
    """국가 원본 JSON에서 필요한 필드만 뽑아내는지 확인한다."""
    raw = {
        "name": "Korea (Republic of)",
        "capital": "Seoul",
        "region": "Asia",
        "population": 51780579,
        "area": 100210,
        "currencies": [{"code": "KRW", "name": "South Korean won"}],
    }
    fields = extract_country_fields(raw)
    assert fields["capital"] == "Seoul"
    assert fields["currency_code"] == "KRW"


def test_extract_ip_fields_converts_camel_case() -> None:
    """ip-api의 camelCase 필드(regionName)를 snake_case로 변환하는지 확인한다."""
    raw = {
        "query": "8.8.8.8",
        "status": "success",
        "country": "United States",
        "regionName": "Virginia",
        "city": "Ashburn",
        "isp": "Google LLC",
        "lat": 39.03,
        "lon": -77.5,
    }
    fields = extract_ip_fields(raw)
    assert fields["region_name"] == "Virginia"


def test_validate_weather_rows_separates_valid_and_invalid() -> None:
    """정상 행과 범위를 벗어난 행이 각각 valid/errors로 분리되는지 확인한다."""
    rows = [
        {"time": "2026-08-06T00:00", "temperature_2m": 25.0, "precipitation_probability": 10},
        {"time": "2026-08-06T01:00", "temperature_2m": 25.0, "precipitation_probability": 200},
    ]
    valid, errors = validate_weather_rows(rows)
    assert len(valid) == 1
    assert len(errors) == 1


def test_build_report_rows_broadcasts_context_columns() -> None:
    """날씨 행 개수만큼 국가/IP 컨텍스트 컬럼이 동일하게 반복되는지 확인한다."""
    rows = [
        {"time": "2026-08-06T00:00", "temperature_2m": 25.0, "precipitation_probability": 10},
        {"time": "2026-08-06T01:00", "temperature_2m": 24.0, "precipitation_probability": 20},
    ]
    valid, _ = validate_weather_rows(rows)
    country = CountryInfo(
        name="Korea", capital="Seoul", region="Asia",
        population=51780579, area=100210, currency_code="KRW",
    )
    ip_location = IpLocation(
        query="8.8.8.8", status="success", country="United States",
        region_name="Virginia", city="Ashburn", isp="Google LLC", lat=39.03, lon=-77.5,
    )
    report_rows = build_report_rows(valid, country, ip_location)
    assert len(report_rows) == 2
    assert all(row.capital == "Seoul" for row in report_rows)
