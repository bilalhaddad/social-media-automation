"""
Maritime advisories JSON connector for Peace Map platform
"""

import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import hashlib

from .base import BaseIngestionConnector, Event, EventCategory, EventSeverity

logger = logging.getLogger(__name__)


class MaritimeConnector(BaseIngestionConnector):
    """Maritime advisories JSON connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("maritime", config)
        self.api_url = config.get("api_url")
        self.json_file_path = config.get("json_file_path")
        self.advisory_types = config.get("advisory_types", ["security", "weather", "navigation"])
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "Peace Map Maritime Connector/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def validate_config(self) -> bool:
        """Validate maritime connector configuration"""
        if not self.api_url and not self.json_file_path:
            logger.error("Maritime connector requires either api_url or json_file_path")
            return False
        
        return True
    
    async def fetch_events(self, since: Optional[datetime] = None) -> List[Event]:
        """Fetch maritime advisory events"""
        if not self.session and self.api_url:
            raise RuntimeError("Maritime connector not initialized. Use async context manager.")
        
        events = []
        
        try:
            # Read maritime data
            maritime_data = await self._read_maritime_data()
            
            # Parse advisories
            for advisory in maritime_data:
                try:
                    event = self._parse_maritime_advisory(advisory, since)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.error(f"Error parsing maritime advisory: {str(e)}")
                    continue
            
            await self.update_last_fetch_time()
            return events
            
        except Exception as e:
            logger.error(f"Error fetching maritime events: {str(e)}")
            return []
    
    async def _read_maritime_data(self) -> List[Dict[str, Any]]:
        """Read maritime data from API or file"""
        if self.json_file_path:
            return await self._read_json_file()
        elif self.api_url:
            return await self._read_json_api()
        else:
            return []
    
    async def _read_json_file(self) -> List[Dict[str, Any]]:
        """Read JSON data from local file"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # Handle both single objects and arrays
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
                else:
                    return []
        except Exception as e:
            logger.error(f"Error reading JSON file {self.json_file_path}: {str(e)}")
            return []
    
    async def _read_json_api(self) -> List[Dict[str, Any]]:
        """Read JSON data from API"""
        try:
            async with self.session.get(self.api_url) as response:
                if response.status != 200:
                    logger.error(f"Maritime API returned status {response.status}")
                    return []
                
                data = await response.json()
                # Handle both single objects and arrays
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
                else:
                    return []
        except Exception as e:
            logger.error(f"Error reading JSON from API {self.api_url}: {str(e)}")
            return []
    
    def _parse_maritime_advisory(self, advisory: Dict[str, Any], since: Optional[datetime] = None) -> Optional[Event]:
        """Parse maritime advisory into Event"""
        try:
            # Extract basic information
            title = advisory.get("title", advisory.get("subject", "Maritime Advisory"))
            description = advisory.get("description", advisory.get("content", ""))
            
            # Parse advisory date
            advisory_date = self._parse_advisory_date(advisory)
            if since and advisory_date and advisory_date < since:
                return None
            
            # Extract location
            location = self._extract_maritime_location(advisory)
            
            # Classify event
            category = self._classify_maritime_event(advisory)
            severity = self._assess_maritime_severity(advisory)
            
            # Calculate confidence
            confidence = self._calculate_maritime_confidence(advisory)
            
            # Generate unique ID
            event_id = self._generate_maritime_event_id(advisory)
            
            # Extract tags
            tags = self._extract_maritime_tags(advisory)
            
            # Create event
            event = Event(
                id=event_id,
                title=title,
                description=description,
                source="Maritime Advisory",
                source_url=advisory.get("url"),
                published_at=advisory_date or datetime.utcnow(),
                location=location,
                category=category,
                severity=severity,
                confidence=confidence,
                raw_data=advisory,
                tags=tags
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error parsing maritime advisory: {str(e)}")
            return None
    
    def _parse_advisory_date(self, advisory: Dict[str, Any]) -> Optional[datetime]:
        """Parse advisory date from maritime data"""
        date_fields = ["date", "published", "issued", "timestamp", "created_at"]
        
        for field in date_fields:
            date_value = advisory.get(field)
            if date_value:
                try:
                    # Try common date formats
                    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]:
                        try:
                            return datetime.strptime(str(date_value), fmt).replace(tzinfo=timezone.utc)
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None
    
    def _extract_maritime_location(self, advisory: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract location from maritime advisory"""
        location = {}
        
        # Extract port information
        port = advisory.get("port", advisory.get("harbor", advisory.get("location")))
        if port:
            location["port"] = port
        
        # Extract country/region
        country = advisory.get("country", advisory.get("region", advisory.get("nation")))
        if country:
            location["country"] = country
        
        # Extract coordinates
        lat = advisory.get("latitude", advisory.get("lat"))
        lon = advisory.get("longitude", advisory.get("lon", advisory.get("lng")))
        
        if lat and lon:
            try:
                location["lat"] = float(lat)
                location["lon"] = float(lon)
            except (ValueError, TypeError):
                pass
        
        # Extract area/zone information
        area = advisory.get("area", advisory.get("zone", advisory.get("region")))
        if area:
            location["area"] = area
        
        return location if location else None
    
    def _classify_maritime_event(self, advisory: Dict[str, Any]) -> EventCategory:
        """Classify maritime advisory event"""
        # Check advisory type
        advisory_type = advisory.get("type", advisory.get("category", "")).lower()
        
        if "security" in advisory_type or "threat" in advisory_type:
            return EventCategory.KINETIC
        elif "cyber" in advisory_type or "digital" in advisory_type:
            return EventCategory.CYBER
        elif "protest" in advisory_type or "demonstration" in advisory_type:
            return EventCategory.PROTEST
        elif "economic" in advisory_type or "trade" in advisory_type:
            return EventCategory.ECONOMIC
        elif "environment" in advisory_type or "weather" in advisory_type:
            return EventCategory.ENVIRONMENTAL
        elif "political" in advisory_type or "policy" in advisory_type:
            return EventCategory.POLITICAL
        
        # Fallback to content-based classification
        title = advisory.get("title", "")
        description = advisory.get("description", "")
        return self._classify_event(title, description)
    
    def _assess_maritime_severity(self, advisory: Dict[str, Any]) -> EventSeverity:
        """Assess maritime advisory severity"""
        # Check severity field
        severity_field = advisory.get("severity", advisory.get("level", advisory.get("priority", ""))).lower()
        
        if severity_field in ["critical", "emergency", "urgent"]:
            return EventSeverity.CRITICAL
        elif severity_field in ["high", "severe", "important"]:
            return EventSeverity.HIGH
        elif severity_field in ["medium", "moderate", "normal"]:
            return EventSeverity.MEDIUM
        elif severity_field in ["low", "minor", "info"]:
            return EventSeverity.LOW
        
        # Check for severity indicators in content
        title = advisory.get("title", "")
        description = advisory.get("description", "")
        content = f"{title} {description}".lower()
        
        if any(keyword in content for keyword in ["emergency", "critical", "urgent", "immediate"]):
            return EventSeverity.CRITICAL
        elif any(keyword in content for keyword in ["warning", "alert", "caution", "danger"]):
            return EventSeverity.HIGH
        elif any(keyword in content for keyword in ["advisory", "notice", "information"]):
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW
    
    def _calculate_maritime_confidence(self, advisory: Dict[str, Any]) -> float:
        """Calculate confidence for maritime advisory"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on data completeness
        if advisory.get("title"):
            confidence += 0.1
        if advisory.get("description"):
            confidence += 0.1
        if advisory.get("port") or advisory.get("location"):
            confidence += 0.1
        if advisory.get("date") or advisory.get("published"):
            confidence += 0.1
        if advisory.get("authority") or advisory.get("source"):
            confidence += 0.1
        
        # Check for official sources
        authority = advisory.get("authority", advisory.get("source", ""))
        if authority and any(term in authority.lower() for term in ["coast guard", "navy", "maritime", "port authority"]):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_maritime_tags(self, advisory: Dict[str, Any]) -> List[str]:
        """Extract tags from maritime advisory"""
        tags = []
        
        # Add advisory type tag
        advisory_type = advisory.get("type", advisory.get("category"))
        if advisory_type:
            tags.append(f"advisory_type:{advisory_type}")
        
        # Add port tag
        port = advisory.get("port", advisory.get("harbor"))
        if port:
            tags.append(f"port:{port}")
        
        # Add country tag
        country = advisory.get("country", advisory.get("region"))
        if country:
            tags.append(f"country:{country}")
        
        # Add authority tag
        authority = advisory.get("authority", advisory.get("source"))
        if authority:
            tags.append(f"authority:{authority}")
        
        # Add severity tag
        severity = advisory.get("severity", advisory.get("level"))
        if severity:
            tags.append(f"severity:{severity}")
        
        return tags
    
    def _generate_maritime_event_id(self, advisory: Dict[str, Any]) -> str:
        """Generate unique ID for maritime advisory"""
        # Try to use existing ID
        advisory_id = advisory.get("id", advisory.get("advisory_id"))
        if advisory_id:
            return f"maritime_{advisory_id}"
        
        # Fallback to hash of key fields
        key_fields = [
            advisory.get("title", ""),
            advisory.get("port", ""),
            advisory.get("date", ""),
            advisory.get("authority", "")
        ]
        key_string = ":".join(str(field) for field in key_fields if field)
        return f"maritime_{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def _normalize_event_data(self, advisory: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize maritime advisory data for storage"""
        return {
            "advisory_data": advisory,
            "source_file": self.json_file_path or self.api_url,
            "ingestion_time": datetime.utcnow().isoformat()
        }
