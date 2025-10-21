"""
GDELT 2.0 connector for Peace Map platform
"""

import asyncio
import aiohttp
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging
import hashlib

from .base import BaseIngestionConnector, Event, EventCategory, EventSeverity

logger = logging.getLogger(__name__)


class GDELTConnector(BaseIngestionConnector):
    """GDELT 2.0 database connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("gdelt", config)
        self.api_url = config.get("api_url", "https://api.gdeltproject.org/api/v2")
        self.session: Optional[aiohttp.ClientSession] = None
        self.default_query_params = config.get("query_params", {})
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={"User-Agent": "Peace Map GDELT Connector/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def validate_config(self) -> bool:
        """Validate GDELT connector configuration"""
        if not self.api_url:
            logger.error("GDELT API URL not configured")
            return False
        
        return True
    
    async def fetch_events(self, since: Optional[datetime] = None) -> List[Event]:
        """Fetch events from GDELT 2.0"""
        if not self.session:
            raise RuntimeError("GDELT connector not initialized. Use async context manager.")
        
        events = []
        
        # Build query parameters
        query_params = self._build_query_params(since)
        
        try:
            # Fetch events from GDELT
            gdelt_events = await self._fetch_gdelt_data(query_params)
            
            # Convert to standard Event format
            for gdelt_event in gdelt_events:
                try:
                    event = self._convert_gdelt_event(gdelt_event)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.error(f"Error converting GDELT event: {str(e)}")
                    continue
            
            await self.update_last_fetch_time()
            return events
            
        except Exception as e:
            logger.error(f"Error fetching GDELT events: {str(e)}")
            return []
    
    def _build_query_params(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Build query parameters for GDELT API"""
        params = {
            "format": "json",
            "maxrecords": 250,
            **self.default_query_params
        }
        
        if since:
            # GDELT uses date format YYYYMMDDHHMMSS
            params["startdatetime"] = since.strftime("%Y%m%d%H%M%S")
        
        return params
    
    async def _fetch_gdelt_data(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch data from GDELT API"""
        try:
            # Use GDELT's export endpoint
            url = f"{self.api_url}/doc/doc"
            
            async with self.session.get(url, params=query_params) as response:
                if response.status != 200:
                    logger.error(f"GDELT API returned status {response.status}")
                    return []
                
                data = await response.json()
                
                if "docs" in data:
                    return data["docs"]
                else:
                    logger.warning("No docs found in GDELT response")
                    return []
                
        except Exception as e:
            logger.error(f"Error fetching GDELT data: {str(e)}")
            return []
    
    def _convert_gdelt_event(self, gdelt_event: Dict[str, Any]) -> Optional[Event]:
        """Convert GDELT event to standard Event format"""
        try:
            # Extract basic information
            title = gdelt_event.get("title", "")
            description = gdelt_event.get("snippet", "")
            url = gdelt_event.get("url", "")
            
            # Parse publication date
            published_at = self._parse_gdelt_date(gdelt_event.get("seendate"))
            
            # Extract location
            location = self._extract_gdelt_location(gdelt_event)
            
            # Classify event
            category = self._classify_gdelt_event(gdelt_event)
            severity = self._assess_gdelt_severity(gdelt_event)
            
            # Calculate confidence based on GDELT confidence score
            confidence = self._calculate_gdelt_confidence(gdelt_event)
            
            # Generate unique ID
            event_id = self._generate_gdelt_event_id(gdelt_event)
            
            # Extract tags
            tags = self._extract_gdelt_tags(gdelt_event)
            
            # Create event
            event = Event(
                id=event_id,
                title=title,
                description=description,
                source="GDELT 2.0",
                source_url=url,
                published_at=published_at or datetime.utcnow(),
                location=location,
                category=category,
                severity=severity,
                confidence=confidence,
                raw_data=gdelt_event,
                tags=tags
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error converting GDELT event: {str(e)}")
            return None
    
    def _parse_gdelt_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse GDELT date string"""
        if not date_str:
            return None
        
        try:
            # GDELT dates are typically in format YYYYMMDDHHMMSS
            if len(date_str) == 14:
                return datetime.strptime(date_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            else:
                # Try other common formats
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y%m%d"]:
                    try:
                        return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
        except Exception:
            pass
        
        return None
    
    def _extract_gdelt_location(self, gdelt_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract location from GDELT event"""
        location = {}
        
        # Extract country information
        country = gdelt_event.get("country")
        if country:
            location["country"] = country
        
        # Extract region information
        region = gdelt_event.get("region")
        if region:
            location["region"] = region
        
        # Extract city information
        city = gdelt_event.get("city")
        if city:
            location["city"] = city
        
        # Extract coordinates if available
        lat = gdelt_event.get("latitude")
        lon = gdelt_event.get("longitude")
        if lat and lon:
            try:
                location["lat"] = float(lat)
                location["lon"] = float(lon)
            except (ValueError, TypeError):
                pass
        
        return location if location else None
    
    def _classify_gdelt_event(self, gdelt_event: Dict[str, Any]) -> EventCategory:
        """Classify GDELT event based on available fields"""
        # Use GDELT's event code if available
        event_code = gdelt_event.get("eventcode")
        if event_code:
            # GDELT event codes mapping
            if event_code.startswith("14"):  # Protest
                return EventCategory.PROTEST
            elif event_code.startswith("19"):  # Use unconventional mass violence
                return EventCategory.KINETIC
            elif event_code.startswith("16"):  # Coerce
                return EventCategory.POLITICAL
            elif event_code.startswith("17"):  # Assault
                return EventCategory.KINETIC
        
        # Fallback to content-based classification
        title = gdelt_event.get("title", "")
        description = gdelt_event.get("snippet", "")
        return self._classify_event(title, description)
    
    def _assess_gdelt_severity(self, gdelt_event: Dict[str, Any]) -> EventSeverity:
        """Assess severity based on GDELT event data"""
        # Use GDELT's Goldstein scale if available
        goldstein_scale = gdelt_event.get("goldsteinscale")
        if goldstein_scale is not None:
            try:
                score = float(goldstein_scale)
                if score <= -5:
                    return EventSeverity.CRITICAL
                elif score <= -2:
                    return EventSeverity.HIGH
                elif score <= 0:
                    return EventSeverity.MEDIUM
                else:
                    return EventSeverity.LOW
            except (ValueError, TypeError):
                pass
        
        # Fallback to content-based assessment
        title = gdelt_event.get("title", "")
        description = gdelt_event.get("snippet", "")
        return self._assess_severity(title, description)
    
    def _calculate_gdelt_confidence(self, gdelt_event: Dict[str, Any]) -> float:
        """Calculate confidence based on GDELT data quality"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on data completeness
        if gdelt_event.get("title"):
            confidence += 0.1
        if gdelt_event.get("snippet"):
            confidence += 0.1
        if gdelt_event.get("url"):
            confidence += 0.1
        if gdelt_event.get("country"):
            confidence += 0.1
        if gdelt_event.get("seendate"):
            confidence += 0.1
        
        # Use GDELT's own confidence if available
        gdelt_confidence = gdelt_event.get("confidence")
        if gdelt_confidence is not None:
            try:
                gdelt_conf = float(gdelt_confidence)
                confidence = (confidence + gdelt_conf) / 2
            except (ValueError, TypeError):
                pass
        
        return min(confidence, 1.0)
    
    def _extract_gdelt_tags(self, gdelt_event: Dict[str, Any]) -> List[str]:
        """Extract tags from GDELT event"""
        tags = []
        
        # Add event type tags
        event_type = gdelt_event.get("eventtype")
        if event_type:
            tags.append(f"event_type:{event_type}")
        
        # Add country tags
        country = gdelt_event.get("country")
        if country:
            tags.append(f"country:{country}")
        
        # Add region tags
        region = gdelt_event.get("region")
        if region:
            tags.append(f"region:{region}")
        
        # Add source tags
        source = gdelt_event.get("source")
        if source:
            tags.append(f"source:{source}")
        
        return tags
    
    def _generate_gdelt_event_id(self, gdelt_event: Dict[str, Any]) -> str:
        """Generate unique ID for GDELT event"""
        # Use GDELT's global event ID if available
        global_event_id = gdelt_event.get("globaleventid")
        if global_event_id:
            return f"gdelt_{global_event_id}"
        
        # Fallback to hash of key fields
        key_fields = [
            gdelt_event.get("title", ""),
            gdelt_event.get("url", ""),
            gdelt_event.get("seendate", "")
        ]
        key_string = ":".join(str(field) for field in key_fields)
        return f"gdelt_{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def _normalize_event_data(self, gdelt_event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize GDELT event data for storage"""
        return {
            "globaleventid": gdelt_event.get("globaleventid"),
            "eventcode": gdelt_event.get("eventcode"),
            "eventtype": gdelt_event.get("eventtype"),
            "goldsteinscale": gdelt_event.get("goldsteinscale"),
            "nummentions": gdelt_event.get("nummentions"),
            "numsources": gdelt_event.get("numsources"),
            "numarticles": gdelt_event.get("numarticles"),
            "avgtone": gdelt_event.get("avgtone"),
            "country": gdelt_event.get("country"),
            "region": gdelt_event.get("region"),
            "city": gdelt_event.get("city"),
            "latitude": gdelt_event.get("latitude"),
            "longitude": gdelt_event.get("longitude"),
            "source": gdelt_event.get("source"),
            "seendate": gdelt_event.get("seendate"),
            "raw_data": gdelt_event
        }
