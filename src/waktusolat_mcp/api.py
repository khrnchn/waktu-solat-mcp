"""Async HTTP client for the Waktu Solat Malaysia API."""

import httpx
from typing import Any


class WaktuSolatAPIError(Exception):
    """Raised when the Waktu Solat API returns an error."""

    pass


class WaktuSolatAPI:
    """Async client for https://api.waktusolat.app"""

    BASE_URL = "https://api.waktusolat.app"
    TIMEOUT = 30.0

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[str, Any] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=self.TIMEOUT,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _fetch(self, url: str) -> dict[str, Any]:
        """Fetch JSON from URL with caching."""
        if url in self._cache:
            return self._cache[url]
        client = await self._get_client()
        response = await client.get(url)
        if response.status_code != 200:
            raise WaktuSolatAPIError(
                f"API request failed: {response.status_code} {response.reason_phrase} for {url}"
            )
        data = response.json()
        self._cache[url] = data
        return data

    async def get_prayer_times(
        self, zone: str, year: int | None = None, month: int | None = None
    ) -> dict[str, Any]:
        """
        Fetch prayer times for a zone.
        If year and month are omitted, returns current month.
        """
        zone = zone.upper()
        if year is not None and month is not None:
            url = f"/v2/solat/{zone}?year={year}&month={month}"
        else:
            url = f"/v2/solat/{zone}"
        return await self._fetch(url)

    async def get_zones(self, state: str | None = None) -> list[dict[str, Any]]:
        """
        Fetch zone codes with descriptions.
        If state is provided, filter by state code (e.g. SGR, JHR).
        """
        if state:
            state = state.upper()
            url = f"/zones/{state}"
        else:
            url = "/zones"
        data = await self._fetch(url)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "zones" in data:
            return data["zones"]
        return [data] if isinstance(data, dict) else []
