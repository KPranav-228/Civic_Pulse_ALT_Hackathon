"""RSS Feed and Web Scraping ingestion service for CivicPulse."""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RSSIngestionService:
    """Fetches and parses live civic news from RSS feeds and target URLs."""

    def __init__(self):
        self.default_feeds = [
            "https://news.google.com/rss/search?q=traffic+Hyderabad+OR+road+closure&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=water+supply+Bangalore+OR+power+cut&hl=en-IN&gl=IN&ceid=IN:en",
        ]

    async def fetch_article_text(self, url: str) -> Optional[Dict[str, str]]:
        """Fetch an external URL and extract primary article body using BeautifulSoup."""
        headers = {
            "User-Agent": "CivicPulse/1.0 (Public Safety & Civic Threat Ingestion Bot)"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: status {resp.status_code}")
                    return None

                soup = BeautifulSoup(resp.text, "html.parser")

                # Remove non-content elements
                for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    element.decompose()

                title = soup.title.string.strip() if soup.title and soup.title.string else "External Article"

                # Extract paragraphs
                paragraphs = [p.get_text().strip() for p in soup.find_all("p")]
                article_body = " ".join([p for p in paragraphs if len(p) > 20])

                if len(article_body) < 50:
                    # Fallback to body text
                    article_body = soup.body.get_text(separator=" ", strip=True) if soup.body else ""

                return {
                    "title": title[:120],
                    "text": article_body[:4000],  # Truncate to reasonable length
                    "url": url,
                    "domain": urlparse(url).netloc
                }
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return None

    def parse_feed_entries(self, feed_url: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Parse an RSS feed and return normalized news entries."""
        feed = feedparser.parse(feed_url)
        entries = []

        for entry in feed.entries[:limit]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            # Clean HTML from summary
            soup = BeautifulSoup(summary, "html.parser")
            clean_summary = soup.get_text()

            full_text = f"{title}. {clean_summary}".strip()
            entries.append({
                "title": title,
                "text": full_text,
                "link": entry.get("link", ""),
                "published": entry.get("published", None),
                "source": feed.feed.get("title", "RSS Feed")
            })

        return entries


rss_service = RSSIngestionService()
