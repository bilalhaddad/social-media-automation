"""
ACLED-style CSV connector for Peace Map platform
"""

import csv
import io
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import hashlib

from .base import BaseIngestionConnector, Event, EventCategory, EventSeverity

logger = logging.getLogger(__name__)


class ACLEDConnector(BaseIngestionConnector):
    """ACLED-style CSV data connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("acled", config)
        self.csv_url = config.get("csv_url")
        self.csv_file_path = config.get("csv_file_path")
        self.field_mapping = config.get("field_mapping", {})
        self.default_country = config.get("default_country", "Unknown")
        self.default_region = config.get("default_region", "Unknown")
    
    def validate_config(self) -> bool:
        """Validate ACLED connector configuration"""
        if not self.csv_url and not self.csv_file_path:
            logger.error("ACLED connector requires either csv_url or csv_file_path")
            return False
        
        return True
    
    async def fetch_events(self, since: Optional[datetime] = None) -> List[Event]:
        """Fetch events from ACLED-style CSV data"""
        events = []
        
        try:
            # Read CSV data
            csv_data = await self._read_csv_data()
            
            # Parse CSV rows
            for row in csv_data:
                try:
                    event = self._parse_csv_row(row, since)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.error(f"Error parsing ACLED CSV row: {str(e)}")
                    continue
            
            await self.update_last_fetch_time()
            return events
            
        except Exception as e:
            logger.error(f"Error fetching ACLED events: {str(e)}")
            return []
    
    async def _read_csv_data(self) -> List[Dict[str, Any]]:
        """Read CSV data from URL or file"""
        if self.csv_file_path:
            return await self._read_csv_file()
        elif self.csv_url:
            return await self._read_csv_url()
        else:
            return []
    
    async def _read_csv_file(self) -> List[Dict[str, Any]]:
        """Read CSV data from local file"""
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                return list(reader)
        except Exception as e:
            logger.error(f"Error reading CSV file {self.csv_file_path}: {str(e)}")
            return []
    
    async def _read_csv_url(self) -> List[Dict[str, Any]]:
        """Read CSV data from URL"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.csv_url) as response:
                    if response.status != 200:
                        logger.error(f"CSV URL returned status {response.status}")
                        return []
                    
                    content = await response.text()
                    reader = csv.DictReader(io.StringIO(content))
                    return list(reader)
        except Exception as e:
            logger.error(f"Error reading CSV from URL {self.csv_url}: {str(e)}")
            return []
    
    def _parse_csv_row(self, row: Dict[str, Any], since: Optional[datetime] = None) -> Optional[Event]:
        """Parse a single CSV row into an Event"""
        try:
            # Extract basic information using field mapping
            title = self._get_field_value(row, "title", "event", "event_name")
            description = self._get_field_value(row, "description", "notes", "summary")
            
            # Parse event date
            event_date = self._parse_event_date(row)
            if since and event_date and event_date < since:
                return None
            
            # Extract location
            location = self._extract_csv_location(row)
            
            # Classify event
            category = self._classify_csv_event(row)
            severity = self._assess_csv_severity(row)
            
            # Calculate confidence
            confidence = self._calculate_csv_confidence(row)
            
            # Generate unique ID
            event_id = self._generate_csv_event_id(row)
            
            # Extract tags
            tags = self._extract_csv_tags(row)
            
            # Create event
            event = Event(
                id=event_id,
                title=title or "ACLED Event",
                description=description or "",
                source="ACLED",
                source_url=None,
                published_at=event_date or datetime.utcnow(),
                location=location,
                category=category,
                severity=severity,
                confidence=confidence,
                raw_data=row,
                tags=tags
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error parsing ACLED CSV row: {str(e)}")
            return None
    
    def _get_field_value(self, row: Dict[str, Any], *field_names: str) -> Optional[str]:
        """Get field value using multiple possible field names"""
        for field_name in field_names:
            if field_name in row and row[field_name]:
                return str(row[field_name]).strip()
        return None
    
    def _parse_event_date(self, row: Dict[str, Any]) -> Optional[datetime]:
        """Parse event date from CSV row"""
        date_fields = ["event_date", "date", "timestamp", "occurred_on"]
        
        for field in date_fields:
            date_value = self._get_field_value(row, field)
            if date_value:
                try:
                    # Try common date formats
                    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]:
                        try:
                            return datetime.strptime(date_value, fmt).replace(tzinfo=timezone.utc)
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None
    
    def _extract_csv_location(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract location from CSV row"""
        location = {}
        
        # Extract country
        country = self._get_field_value(row, "country", "country_name", "nation")
        if country:
            location["country"] = country
        else:
            location["country"] = self.default_country
        
        # Extract region/state
        region = self._get_field_value(row, "region", "state", "admin1", "admin2")
        if region:
            location["region"] = region
        else:
            location["region"] = self.default_region
        
        # Extract city
        city = self._get_field_value(row, "city", "location", "place")
        if city:
            location["city"] = city
        
        # Extract coordinates
        lat = self._get_field_value(row, "latitude", "lat", "y")
        lon = self._get_field_value(row, "longitude", "lon", "lng", "x")
        
        if lat and lon:
            try:
                location["lat"] = float(lat)
                location["lon"] = float(lon)
            except (ValueError, TypeError):
                pass
        
        return location if location else None
    
    def _classify_csv_event(self, row: Dict[str, Any]) -> EventCategory:
        """Classify event based on CSV data"""
        # Check for event type field
        event_type = self._get_field_value(row, "event_type", "type", "category")
        if event_type:
            event_type_lower = event_type.lower()
            if "protest" in event_type_lower or "demonstration" in event_type_lower:
                return EventCategory.PROTEST
            elif "violence" in event_type_lower or "attack" in event_type_lower:
                return EventCategory.KINETIC
            elif "cyber" in event_type_lower:
                return EventCategory.CYBER
            elif "economic" in event_type_lower:
                return EventCategory.ECONOMIC
            elif "environment" in event_type_lower:
                return EventCategory.ENVIRONMENTAL
            elif "political" in event_type_lower:
                return EventCategory.POLITICAL
        
        # Fallback to content-based classification
        title = self._get_field_value(row, "title", "event", "event_name")
        description = self._get_field_value(row, "description", "notes", "summary")
        return self._classify_event(title or "", description or "")
    
    def _assess_csv_severity(self, row: Dict[str, Any]) -> EventSeverity:
        """Assess severity based on CSV data"""
        # Check for fatalities field
        fatalities = self._get_field_value(row, "fatalities", "deaths", "killed")
        if fatalities:
            try:
                fatality_count = int(fatalities)
                if fatality_count >= 100:
                    return EventSeverity.CRITICAL
                elif fatality_count >= 10:
                    return EventSeverity.HIGH
                elif fatality_count >= 1:
                    return EventSeverity.MEDIUM
            except (ValueError, TypeError):
                pass
        
        # Check for event type severity indicators
        event_type = self._get_field_value(row, "event_type", "type", "category")
        if event_type:
            event_type_lower = event_type.lower()
            if "massacre" in event_type_lower or "mass killing" in event_type_lower:
                return EventSeverity.CRITICAL
            elif "battle" in event_type_lower or "armed conflict" in event_type_lower:
                return EventSeverity.HIGH
            elif "violence" in event_type_lower or "attack" in event_type_lower:
                return EventSeverity.MEDIUM
        
        # Fallback to content-based assessment
        title = self._get_field_value(row, "title", "event", "event_name")
        description = self._get_field_value(row, "description", "notes", "summary")
        return self._assess_severity(title or "", description or "")
    
    def _calculate_csv_confidence(self, row: Dict[str, Any]) -> float:
        """Calculate confidence based on CSV data quality"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on data completeness
        if self._get_field_value(row, "title", "event", "event_name"):
            confidence += 0.1
        if self._get_field_value(row, "description", "notes", "summary"):
            confidence += 0.1
        if self._get_field_value(row, "country", "country_name"):
            confidence += 0.1
        if self._get_field_value(row, "event_date", "date"):
            confidence += 0.1
        if self._get_field_value(row, "latitude", "lat") and self._get_field_value(row, "longitude", "lon"):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_csv_tags(self, row: Dict[str, Any]) -> List[str]:
        """Extract tags from CSV row"""
        tags = []
        
        # Add country tag
        country = self._get_field_value(row, "country", "country_name")
        if country:
            tags.append(f"country:{country}")
        
        # Add region tag
        region = self._get_field_value(row, "region", "state", "admin1")
        if region:
            tags.append(f"region:{region}")
        
        # Add event type tag
        event_type = self._get_field_value(row, "event_type", "type", "category")
        if event_type:
            tags.append(f"event_type:{event_type}")
        
        # Add actor tags
        actor1 = self._get_field_value(row, "actor1", "perpetrator")
        if actor1:
            tags.append(f"actor:{actor1}")
        
        actor2 = self._get_field_value(row, "actor2", "target")
        if actor2:
            tags.append(f"target:{actor2}")
        
        return tags
    
    def _generate_csv_event_id(self, row: Dict[str, Any]) -> str:
        """Generate unique ID for CSV event"""
        # Try to use existing ID field
        event_id = self._get_field_value(row, "id", "event_id", "uuid")
        if event_id:
            return f"acled_{event_id}"
        
        # Fallback to hash of key fields
        key_fields = [
            self._get_field_value(row, "title", "event", "event_name"),
            self._get_field_value(row, "event_date", "date"),
            self._get_field_value(row, "country", "country_name"),
            self._get_field_value(row, "latitude", "lat"),
            self._get_field_value(row, "longitude", "lon")
        ]
        key_string = ":".join(str(field) for field in key_fields if field)
        return f"acled_{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def _normalize_event_data(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize CSV row data for storage"""
        return {
            "row_data": row,
            "source_file": self.csv_file_path or self.csv_url,
            "ingestion_time": datetime.utcnow().isoformat()
        }
