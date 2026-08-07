"""httpx.AsyncClient + asyncio.gather()로 3개 API를 동시에 호출한다.

순서대로 하나씩 await하면 응답 시간이 합산되지만, gather()로 묶으면
가장 느린 API 1개의 응답 시간에 가깝게 끝난다.
"""

import asyncio
from typing import Any

import httpx

from app.config import COUNTRIES_DEV_URL, IP_API_URL, OPEN_METEO_PARAMS, OPEN_METEO_URL


class ApiFetchError(RuntimeError):
    """API 요청/응답 관련 예외를 한 종류로 통일해서 호출부를 단순하게 만든다."""


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """공통 GET 요청 헬퍼. 네트워크/HTTP/JSON 오류를 ApiFetchError로 통일한다."""
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()  # 4xx/5xx면 여기서 예외 발생
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise ApiFetchError(f"HTTP 오류 {exc.response.status_code}: {url}") from exc
    except httpx.RequestError as exc:
        raise ApiFetchError(f"네트워크 오류: {url} - {exc}") from exc
    except ValueError as exc:
        raise ApiFetchError(f"JSON 파싱 오류: {url}") from exc


async def fetch_weather(client: httpx.AsyncClient) -> dict[str, Any]:
    """Open-Meteo: 서울 3일치 시간대별 기온/강수확률."""
    return await _get_json(client, OPEN_METEO_URL, params=OPEN_METEO_PARAMS)


async def fetch_country(client: httpx.AsyncClient) -> dict[str, Any]:
    """Countries.dev: 대한민국(KOR) 국가 정보."""
    return await _get_json(client, COUNTRIES_DEV_URL)


async def fetch_ip_location(client: httpx.AsyncClient) -> dict[str, Any]:
    """ip-api: 8.8.8.8의 IP 기반 지역 정보."""
    return await _get_json(client, IP_API_URL)


async def fetch_all(client: httpx.AsyncClient) -> dict[str, dict[str, Any]]:
    """3개 API를 asyncio.gather()로 동시에 호출하고 이름표를 붙여 반환한다."""
    weather, country, ip_location = await asyncio.gather(
        fetch_weather(client),
        fetch_country(client),
        fetch_ip_location(client),
    )
    return {
        "weather": weather,
        "country": country,
        "ip_location": ip_location,
    }
