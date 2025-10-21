"""
RSS/Atom feed connector for Peace Map platform
"""

import feedparser
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse
import logging

from .base import BaseIngestionConnector, Event, EventCategory, EventSeverity

logger = logging.getLogger(__name__)


class RSSConnector(BaseIngestionConnector):
    """RSS/Atom feed connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("rss", config)
        self.feeds = config.get("feeds", [])
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "Peace Map RSS Connector/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def validate_config(self) -> bool:
        """Validate RSS connector configuration"""
        if not self.feeds:
            logger.error("No RSS feeds configured")
            return False
        
        for feed in self.feeds:
            if not feed.get("url"):
                logger.error("RSS feed missing URL")
                return False
            
            # Validate URL format
            try:
                urlparse(feed["url"])
            except Exception:
                logger.error(f"Invalid RSS feed URL: {feed['url']}")
                return False
        
        return True
    
    async def fetch_events(self, since: Optional[datetime] = None) -> List[Event]:
        """Fetch events from RSS feeds"""
        if not self.session:
            raise RuntimeError("RSS connector not initialized. Use async context manager.")
        
        events = []
        
        for feed_config in self.feeds:
            try:
                feed_events = await self._fetch_feed_events(feed_config, since)
                events.extend(feed_events)
            except Exception as e:
                logger.error(f"Error fetching RSS feed {feed_config['url']}: {str(e)}")
                continue
        
        await self.update_last_fetch_time()
        return events
    
    async def _fetch_feed_events(self, feed_config: Dict[str, Any], since: Optional[datetime] = None) -> List[Event]:
        """Fetch events from a single RSS feed"""
        url = feed_config["url"]
        source_name = feed_config.get("name", urlparse(url).netloc)
        categories = feed_config.get("categories", [])
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"RSS feed returned status {response.status}: {url}")
                    return []
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                if feed.bozo:
                    logger.warning(f"RSS feed parsing issues for {url}: {feed.bozo_exception}")
                
                events = []
                for entry in feed.entries:
                    try:
                        event = await self._parse_feed_entry(entry, source_name, categories, since)
                        if event:
                            events.append(event)
                    except Exception as e:
                        logger.error(f"Error parsing RSS entry: {str(e)}")
                        continue
                
                return events
                
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {str(e)}")
            return []
    
    async def _parse_feed_entry(self, entry: Any, source_name: str, categories: List[str], since: Optional[datetime] = None) -> Optional[Event]:
        """Parse a single RSS feed entry into an Event"""
        # Extract basic information
        title = getattr(entry, "title", "")
        description = getattr(entry, "description", "") or getattr(entry, "summary", "")
        link = getattr(entry, "link", "")
        
        # Parse publication date
        published_at = self._parse_pub_date(entry)
        if since and published_at and published_at < since:
            return None
        
        # Extract location if available
        location = self._extract_location_from_entry(entry)
        
        # Classify event
        category = self._classify_event(title, description)
        severity = self._assess_severity(title, description)
        
        # Calculate confidence
        confidence = self._calculate_confidence({
            "title": title,
            "description": description,
            "link": link,
            "published_at": published_at,
            "location": location
        })
        
        # Generate unique ID
        event_id = self._generate_event_id(entry, source_name)
        
        # Extract tags
        tags = self._extract_tags(entry, categories)
        
        # Create event
        event = Event(
            id=event_id,
            title=title,
            description=description,
            source=source_name,
            source_url=link,
            published_at=published_at or datetime.utcnow(),
            location=location,
            category=category,
            severity=severity,
            confidence=confidence,
            raw_data=self._normalize_event_data(entry),
            tags=tags
        )
        
        return event
    
    def _parse_pub_date(self, entry: Any) -> Optional[datetime]:
        """Parse publication date from RSS entry"""
        # Try different date fields
        date_fields = ["published_parsed", "updated_parsed", "created_parsed"]
        
        for field in date_fields:
            if hasattr(entry, field):
                date_tuple = getattr(entry, field)
                if date_tuple:
                    try:
                        return datetime(*date_tuple[:6], tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        continue
        
        # Try string date parsing
        date_strings = ["published", "updated", "created"]
        for field in date_strings:
            if hasattr(entry, field):
                date_str = getattr(entry, field)
                if date_str:
                    try:
                        # Try common date formats
                        for fmt in ["%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                            try:
                                return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                            except ValueError:
                                continue
                    except Exception:
                        continue
        
        return None
    
    def _extract_location_from_entry(self, entry: Any) -> Optional[Dict[str, Any]]:
        """Extract location information from RSS entry"""
        # Check for common location fields
        location_fields = ["location", "geo", "place", "country", "region"]
        
        for field in location_fields:
            if hasattr(entry, field):
                location_data = getattr(entry, field)
                if location_data:
                    return self._parse_location_data(location_data)
        
        # Check for geo tags
        if hasattr(entry, "geo_lat") and hasattr(entry, "geo_long"):
            try:
                return {
                    "lat": float(entry.geo_lat),
                    "lon": float(entry.geo_long),
                    "source": "geo_tags"
                }
            except (ValueError, TypeError):
                pass
        
        return None
    
    def _parse_location_data(self, location_data: Any) -> Optional[Dict[str, Any]]:
        """Parse location data from various formats"""
        if isinstance(location_data, dict):
            return location_data
        elif isinstance(location_data, str):
            # Try to parse string location
            # This is a simplified implementation
            return {"name": location_data, "source": "string"}
        
        return None
    
    def _extract_tags(self, entry: Any, default_categories: List[str]) -> List[str]:
        """Extract tags from RSS entry"""
        tags = list(default_categories)
        
        # Extract tags from entry
        if hasattr(entry, "tags"):
            for tag in entry.tags:
                if hasattr(tag, "term"):
                    tags.append(tag.term)
                elif isinstance(tag, str):
                    tags.append(tag)
        
        # Extract categories
        if hasattr(entry, "categories"):
            tags.extend(entry.categories)
        
        return list(set(tags))  # Remove duplicates
    
    def _generate_event_id(self, entry: Any, source_name: str) -> str:
        """Generate unique event ID"""
        # Use link if available, otherwise use title hash
        if hasattr(entry, "link") and entry.link:
            import hashlib
            return hashlib.md5(f"{source_name}:{entry.link}".encode()).hexdigest()
        else:
            import hashlib
            title = getattr(entry, "title", "")
            return hashlib.md5(f"{source_name}:{title}".encode()).hexdigest()
    
    def _normalize_event_data(self, entry: Any) -> Dict[str, Any]:
        """Normalize RSS entry data"""
        return {
            "title": getattr(entry, "title", ""),
            "description": getattr(entry, "description", ""),
            "link": getattr(entry, "link", ""),
            "published": getattr(entry, "published", ""),
            "author": getattr(entry, "author", ""),
            "tags": [tag.term if hasattr(tag, "term") else str(tag) for tag in getattr(entry, "tags", [])],
            "categories": getattr(entry, "categories", []),
            "raw_entry": dict(entry) if hasattr(entry, "__dict__") else str(entry)
        }
