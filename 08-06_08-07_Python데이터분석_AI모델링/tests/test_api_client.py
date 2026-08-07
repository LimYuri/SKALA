"""실제 인터넷 호출 없이(httpx.MockTransport) 비동기 수집 로직을 검증한다."""

import httpx
import pytest

from app.api_client import fetch_all


@pytest.mark.asyncio
async def test_fetch_all_calls_three_urls_concurrently() -> None:
    """fetch_all()이 3개 URL 모두를 호출하고, 각 키에 알맞은 값을 담는지 확인한다."""
    called_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        called_urls.append(str(request.url))
        if "open-meteo" in str(request.url):
            payload = {
                "hourly": {
                    "time": [],
                    "temperature_2m": [],
                    "precipitation_probability": [],
                }
            }
        elif "countries.dev" in str(request.url):
            payload = {"name": "Korea"}
        else:
            payload = {"status": "success", "query": "8.8.8.8"}
        return httpx.Response(status_code=200, json=payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_all(client)

    assert len(called_urls) == 3
    assert result["weather"]["hourly"]["time"] == []
    assert result["country"]["name"] == "Korea"
    assert result["ip_location"]["status"] == "success"
