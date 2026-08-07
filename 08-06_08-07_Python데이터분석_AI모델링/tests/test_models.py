"""Pydantic v2 모델의 타입·범위 검증이 실제로 동작하는지 확인한다."""

import pytest
from pydantic import ValidationError

from app.models import CountryInfo, IpLocation, WeatherHour


def test_weather_hour_accepts_valid_range() -> None:
    """정상 범위의 기온/강수확률은 예외 없이 통과해야 한다."""
    hour = WeatherHour.model_validate(
        {"time": "2026-08-06T00:00", "temperature_2m": 28.5, "precipitation_probability": 40}
    )
    assert hour.temperature_2m == 28.5
    assert hour.precipitation_probability == 40


def test_weather_hour_rejects_out_of_range_probability() -> None:
    """강수확률은 0~100 사이여야 하므로 150은 ValidationError가 발생해야 한다."""
    with pytest.raises(ValidationError):
        WeatherHour.model_validate(
            {"time": "2026-08-06T00:00", "temperature_2m": 20, "precipitation_probability": 150}
        )


def test_country_info_rejects_non_positive_population() -> None:
    """인구는 반드시 양수여야 하므로 0 이하는 실패해야 한다."""
    with pytest.raises(ValidationError):
        CountryInfo.model_validate(
            {
                "name": "Korea",
                "capital": "Seoul",
                "region": "Asia",
                "population": 0,
                "area": 100210,
                "currency_code": "KRW",
            }
        )


def test_ip_location_rejects_failed_status() -> None:
    """ip-api가 status="fail"을 내려주면 커스텀 validator가 예외를 던져야 한다."""
    with pytest.raises(ValidationError):
        IpLocation.model_validate(
            {
                "query": "0.0.0.0",
                "status": "fail",
                "country": "",
                "region_name": "",
                "city": "",
                "isp": "",
                "lat": 0,
                "lon": 0,
            }
        )
