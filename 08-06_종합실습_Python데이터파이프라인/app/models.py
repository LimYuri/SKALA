"""3개 API 응답을 검증하기 위한 Pydantic v2 모델을 정의한다.

Field(...)의 ge/le/gt/min_length로 범위 검증을 선언적으로 표현하면
if문을 직접 쓰는 것보다 코드가 짧고 실수가 적어서 이 방식을 썼다.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --------------------------------------------------------------------------
# 1) Open-Meteo - 서울 시간대별 기온/강수확률 한 시점
# --------------------------------------------------------------------------
class WeatherHour(BaseModel):
    """hourly.time / temperature_2m / precipitation_probability를 한 행으로 묶은 모델."""

    time: datetime  # ISO8601 문자열도 자동으로 datetime으로 변환됨
    temperature_2m: float = Field(ge=-40, le=50)  # 서울 기준 현실적인 기온 범위
    precipitation_probability: int = Field(ge=0, le=100)  # 확률(%)이라 0~100만 허용


# --------------------------------------------------------------------------
# 2) Countries.dev - 대한민국 국가 정보 (필요한 필드만 추출한 뒤 검증)
# --------------------------------------------------------------------------
class CountryInfo(BaseModel):
    """국가명·수도·인구·면적처럼 값 자체가 존재/양수인지가 중요한 필드를 검증."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    capital: str = Field(min_length=1)
    region: str = Field(min_length=1)
    population: int = Field(gt=0)  # 인구가 0 이하면 비정상 데이터로 간주
    area: float = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)  # ISO 4217은 3자리

    @field_validator("currency_code")
    @classmethod
    def currency_code_must_be_upper(cls, value: str) -> str:
        """통화 코드는 KRW처럼 대문자만 정상값으로 취급한다."""
        if not value.isupper():
            raise ValueError(f"통화 코드는 대문자여야 합니다: {value}")
        return value


# --------------------------------------------------------------------------
# 3) ip-api - IP 기반 지역 정보
# --------------------------------------------------------------------------
class IpLocation(BaseModel):
    """조회 상태(status)와 위경도 범위까지 함께 검증하는 모델."""

    query: str = Field(min_length=7)  # "8.8.8.8" 정도의 최소 길이
    status: str
    country: str = Field(min_length=1)
    region_name: str = Field(min_length=1)
    city: str = Field(min_length=1)
    isp: str = Field(min_length=1)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

    @field_validator("status")
    @classmethod
    def status_must_be_success(cls, value: str) -> str:
        """ip-api는 실패해도 200을 주고 status만 fail로 내려주는 경우가 있어 따로 검증."""
        if value != "success":
            raise ValueError(f"IP 조회 상태가 success가 아닙니다: {value}")
        return value


# --------------------------------------------------------------------------
# 4) 최종 저장용 병합 레코드 - 날씨 한 시점 + 국가/지역 컨텍스트
# --------------------------------------------------------------------------
class WeatherReportRow(BaseModel):
    """CSV/Parquet에 실제로 저장되는 한 행."""

    time: datetime
    temperature_2m: float
    precipitation_probability: int
    country_name: str
    capital: str
    country_population: int
    ip_query: str
    ip_city: str
    ip_isp: str
