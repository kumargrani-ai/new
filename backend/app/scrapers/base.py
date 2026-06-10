from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
import httpx
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


@dataclass
class ScrapedListing:
    external_id: str
    title: str
    locality: str
    price_lakhs: float
    area_sqft: float
    bedrooms: Optional[int]
    property_type: str
    source: str
    source_url: str = ""
    sub_locality: str = ""
    bathrooms: Optional[int] = None
    furnishing: str = ""
    is_new_launch: bool = False
    posted_date: str = ""       # e.g. "08 Jun 2026"
    contact_number: str = ""    # advertiser contact if available

    @property
    def price_per_sqft(self) -> float:
        if self.area_sqft and self.area_sqft > 0:
            return round((self.price_lakhs * 100000) / self.area_sqft, 2)
        return 0.0


@dataclass
class ScrapeResult:
    source: str
    listings: List[ScrapedListing] = field(default_factory=list)
    status: str = "success"
    error: str = ""


class BaseScraper(ABC):
    source_name: str = ""
    base_url: str = ""

    def __init__(self):
        self.client = httpx.Client(
            headers=HEADERS,
            timeout=30.0,
            follow_redirects=True,
        )

    async def scrape(self) -> ScrapeResult:
        try:
            listings = await self._fetch_listings()
            return ScrapeResult(source=self.source_name, listings=listings, status="success")
        except Exception as e:
            logger.error(f"{self.source_name} scraper failed: {e}")
            return ScrapeResult(source=self.source_name, status="failed", error=str(e))

    @abstractmethod
    async def _fetch_listings(self) -> List[ScrapedListing]:
        pass

    def close(self):
        self.client.close()
