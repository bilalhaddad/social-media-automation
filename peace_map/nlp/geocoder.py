"""
Geocoding processor for Peace Map platform
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

from .base import BaseNLPProcessor, ProcessingResult, ProcessingStatus

logger = logging.getLogger(__name__)


class Geocoder(BaseNLPProcessor):
    """Geocodes location names to coordinates using Nominatim"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("geocoder", config)
        self.nominatim_url = config.get("nominatim_url", "https://nominatim.openstreetmap.org")
        self.user_agent = config.get("user_agent", "Peace Map Geocoder/1.0")
        self.rate_limit_delay = config.get("rate_limit_delay", 1.0)
        self.max_retries = config.get("max_retries", 3)
        self.timeout = config.get("timeout", 10)
        self.session = None
        self.nominatim = None
    
    async def initialize(self):
        """Initialize the geocoder"""
        try:
            # Initialize Nominatim geocoder
            self.nominatim = Nominatim(
                user_agent=self.user_agent,
                timeout=self.timeout
            )
            
            # Initialize HTTP session for API calls
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={"User-Agent": self.user_agent}
            )
            
            self.is_initialized = True
            logger.info("Geocoder initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize geocoder: {str(e)}")
            raise
    
    async def process(self, text: str, **kwargs) -> ProcessingResult:
        """Geocode a single location"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Preprocess text
            location_text = self._preprocess_text(text)
            
            if not location_text:
                return self._create_result(
                    ProcessingStatus.COMPLETED,
                    None,
                    confidence=0.0,
                    metadata={"reason": "empty_location"}
                )
            
            # Geocode location
            location_data = await self._geocode_location(location_text)
            
            if location_data:
                return self._create_result(
                    ProcessingStatus.COMPLETED,
                    location_data,
                    confidence=location_data.get("confidence", 0.8),
                    metadata={
                        "original_text": text,
                        "processed_text": location_text,
                        "geocoding_method": location_data.get("method", "nominatim")
                    }
                )
            else:
                return self._create_result(
                    ProcessingStatus.COMPLETED,
                    None,
                    confidence=0.0,
                    metadata={"reason": "geocoding_failed"}
                )
                
        except Exception as e:
            logger.error(f"Geocoding failed: {str(e)}")
            return self._create_result(
                ProcessingStatus.FAILED,
                None,
                error=str(e)
            )
    
    async def process_batch(self, texts: List[str], **kwargs) -> List[ProcessingResult]:
        """Geocode multiple locations with rate limiting"""
        if not self.is_initialized:
            await self.initialize()
        
        results = []
        
        for i, text in enumerate(texts):
            # Rate limiting
            if i > 0:
                await asyncio.sleep(self.rate_limit_delay)
            
            result = await self.process(text)
            results.append(result)
        
        return results
    
    async def _geocode_location(self, location_text: str) -> Optional[Dict[str, Any]]:
        """Geocode a location using multiple methods"""
        # Try different geocoding approaches
        methods = [
            self._geocode_with_nominatim,
            self._geocode_with_api,
            self._geocode_with_fallback
        ]
        
        for method in methods:
            try:
                result = await method(location_text)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Geocoding method failed: {str(e)}")
                continue
        
        return None
    
    async def _geocode_with_nominatim(self, location_text: str) -> Optional[Dict[str, Any]]:
        """Geocode using Nominatim geocoder"""
        try:
            # Use Nominatim geocoder
            location = self.nominatim.geocode(location_text, exactly_one=True)
            
            if location:
                return {
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "country": self._extract_country(location.raw),
                    "region": self._extract_region(location.raw),
                    "city": self._extract_city(location.raw),
                    "confidence": 0.8,
                    "method": "nominatim",
                    "raw_data": location.raw
                }
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Nominatim geocoding failed: {str(e)}")
        
        return None
    
    async def _geocode_with_api(self, location_text: str) -> Optional[Dict[str, Any]]:
        """Geocode using Nominatim API directly"""
        try:
            url = f"{self.nominatim_url}/search"
            params = {
                "q": location_text,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and len(data) > 0:
                        result = data[0]
                        return {
                            "lat": float(result.get("lat", 0)),
                            "lon": float(result.get("lon", 0)),
                            "country": result.get("address", {}).get("country"),
                            "region": result.get("address", {}).get("state"),
                            "city": result.get("address", {}).get("city"),
                            "confidence": 0.7,
                            "method": "api",
                            "raw_data": result
                        }
        except Exception as e:
            logger.warning(f"API geocoding failed: {str(e)}")
        
        return None
    
    async def _geocode_with_fallback(self, location_text: str) -> Optional[Dict[str, Any]]:
        """Fallback geocoding using simple text matching"""
        # Simple fallback for common locations
        fallback_locations = {
            "united states": {"lat": 39.8283, "lon": -98.5795, "country": "United States"},
            "usa": {"lat": 39.8283, "lon": -98.5795, "country": "United States"},
            "china": {"lat": 35.8617, "lon": 104.1954, "country": "China"},
            "russia": {"lat": 61.5240, "lon": 105.3188, "country": "Russia"},
            "europe": {"lat": 54.5260, "lon": 15.2551, "country": "Europe"},
            "africa": {"lat": 8.7832, "lon": 34.5085, "country": "Africa"},
            "asia": {"lat": 34.0479, "lon": 100.6197, "country": "Asia"},
            "middle east": {"lat": 25.0000, "lon": 45.0000, "country": "Middle East"},
        }
        
        location_lower = location_text.lower()
        for key, coords in fallback_locations.items():
            if key in location_lower:
                return {
                    **coords,
                    "confidence": 0.5,
                    "method": "fallback"
                }
        
        return None
    
    def _extract_country(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract country from Nominatim raw data"""
        address = raw_data.get("address", {})
        return address.get("country") or address.get("country_code")
    
    def _extract_region(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract region/state from Nominatim raw data"""
        address = raw_data.get("address", {})
        return address.get("state") or address.get("region")
    
    def _extract_city(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract city from Nominatim raw data"""
        address = raw_data.get("address", {})
        return address.get("city") or address.get("town") or address.get("village")
    
    def _calculate_confidence(self, result_data: Any, metadata: Dict[str, Any]) -> float:
        """Calculate confidence for geocoding result"""
        if not result_data:
            return 0.0
        
        confidence = result_data.get("confidence", 0.5)
        
        # Adjust confidence based on data completeness
        if result_data.get("country"):
            confidence += 0.1
        if result_data.get("region"):
            confidence += 0.1
        if result_data.get("city"):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Reverse geocode coordinates to location name"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            location = self.nominatim.reverse(f"{lat}, {lon}", exactly_one=True)
            
            if location:
                return {
                    "name": location.address,
                    "country": self._extract_country(location.raw),
                    "region": self._extract_region(location.raw),
                    "city": self._extract_city(location.raw),
                    "raw_data": location.raw
                }
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {str(e)}")
        
        return None
    
    async def geocode_with_bounds(self, location_text: str, bounds: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Geocode location within specific bounds"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Format bounds for Nominatim
            viewbox = f"{bounds['west']},{bounds['south']},{bounds['east']},{bounds['north']}"
            
            url = f"{self.nominatim_url}/search"
            params = {
                "q": location_text,
                "format": "json",
                "limit": 1,
                "addressdetails": 1,
                "viewbox": viewbox,
                "bounded": 1
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and len(data) > 0:
                        result = data[0]
                        return {
                            "lat": float(result.get("lat", 0)),
                            "lon": float(result.get("lon", 0)),
                            "country": result.get("address", {}).get("country"),
                            "region": result.get("address", {}).get("state"),
                            "city": result.get("address", {}).get("city"),
                            "confidence": 0.8,
                            "method": "bounded_api",
                            "raw_data": result
                        }
        except Exception as e:
            logger.error(f"Bounded geocoding failed: {str(e)}")
        
        return None
    
    async def close(self):
        """Close the geocoder and cleanup resources"""
        if self.session:
            await self.session.close()
    
    def get_geocoding_stats(self) -> Dict[str, Any]:
        """Get geocoding statistics"""
        return {
            "nominatim_url": self.nominatim_url,
            "rate_limit_delay": self.rate_limit_delay,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "is_initialized": self.is_initialized
        }
