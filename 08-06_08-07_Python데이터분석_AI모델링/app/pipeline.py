"""원본 JSON에서 필요한 필드만 뽑아 Pydantic 모델로 검증하고, 검증된
값들을 저장용 행(WeatherReportRow) 목록으로 합치는 단계를 담당한다.
"""

from typing import Any

from pydantic import ValidationError

from app.models import CountryInfo, IpLocation, WeatherHour, WeatherReportRow


# --------------------------------------------------------------------------
# 1) 필요한 필드만 추출 (검증 이전 단계)
# --------------------------------------------------------------------------
def extract_weather_rows(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """hourly의 세 배열을 시점별로 zip해서 한 시점당 하나의 dict로 만든다."""
    hourly = raw["hourly"]
    return [
        {
            "time": time_value,
            "temperature_2m": temp_value,
            "precipitation_probability": prob_value,
        }
        for time_value, temp_value, prob_value in zip(
            hourly["time"],
            hourly["temperature_2m"],
            hourly["precipitation_probability"],
            strict=True,  # 세 배열 길이가 다르면 조용히 넘기지 않고 바로 오류
        )
    ]


def extract_country_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """국가 정보 원본 JSON에서 실습에 필요한 필드만 골라낸다."""
    currencies = raw.get("currencies") or [{}]
    return {
        "name": raw.get("name"),
        "capital": raw.get("capital"),
        "region": raw.get("region"),
        "population": raw.get("population"),
        "area": raw.get("area"),
        "currency_code": currencies[0].get("code"),
    }


def extract_ip_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """ip-api 원본 JSON에서 필요한 필드만 골라낸다(camelCase -> snake_case)."""
    return {
        "query": raw.get("query"),
        "status": raw.get("status"),
        "country": raw.get("country"),
        "region_name": raw.get("regionName"),
        "city": raw.get("city"),
        "isp": raw.get("isp"),
        "lat": raw.get("lat"),
        "lon": raw.get("lon"),
    }


# --------------------------------------------------------------------------
# 2) 검증 (Pydantic model_validate가 타입/범위를 자동으로 검사)
# --------------------------------------------------------------------------
def validate_weather_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[WeatherHour], list[dict[str, Any]]]:
    """실패한 행은 버리지 않고 오류 목록에만 기록해서 나머지 처리를 계속한다."""
    valid: list[WeatherHour] = []
    errors: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        try:
            valid.append(WeatherHour.model_validate(row))
        except ValidationError as exc:
            errors.append(
                {
                    "source": "open-meteo",
                    "index": index,
                    "errors": exc.errors(include_url=False),
                }
            )

    return valid, errors


def validate_country(raw: dict[str, Any]) -> CountryInfo:
    """국가 정보는 1건뿐이라 실패하면 그냥 예외를 전파한다."""
    fields = extract_country_fields(raw)
    try:
        return CountryInfo.model_validate(fields)
    except ValidationError as exc:
        raise ValueError(f"국가 정보 검증 실패: {exc.errors(include_url=False)}") from exc


def validate_ip_location(raw: dict[str, Any]) -> IpLocation:
    """IP 위치 정보도 1건뿐이라 실패하면 그냥 예외를 전파한다."""
    fields = extract_ip_fields(raw)
    try:
        return IpLocation.model_validate(fields)
    except ValidationError as exc:
        raise ValueError(f"IP 위치 정보 검증 실패: {exc.errors(include_url=False)}") from exc


# --------------------------------------------------------------------------
# 3) 병합 - 검증이 끝난 세 값을 저장용 행 목록으로 합친다
# --------------------------------------------------------------------------
def build_report_rows(
    weather_rows: list[WeatherHour],
    country: CountryInfo,
    ip_location: IpLocation,
) -> list[WeatherReportRow]:
    """국가/IP는 시간에 안 변하는 값이라 날씨 행 수(72)만큼 그대로 반복해서 붙인다."""
    return [
        WeatherReportRow(
            time=hour.time,
            temperature_2m=hour.temperature_2m,
            precipitation_probability=hour.precipitation_probability,
            country_name=country.name,
            capital=country.capital,
            country_population=country.population,
            ip_query=ip_location.query,
            ip_city=ip_location.city,
            ip_isp=ip_location.isp,
        )
        for hour in weather_rows
    ]
