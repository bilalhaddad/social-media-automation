"""
Port chokepoints layer for Peace Map platform
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseGeoLayer, GeoFeature, GeoBounds, LayerType, LayerStyle

logger = logging.getLogger(__name__)


class PortChokepointsLayer(BaseGeoLayer):
    """Port chokepoints layer showing critical maritime passages"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("port_chokepoints", config)
        self.layer_config.type = LayerType.POINTS
        self.layer_config.style = LayerStyle.CIRCLE
        
        # Port data
        self.ports_file = config.get("ports_file", "data/port_chokepoints.geojson")
        self.ports_data: List[Dict[str, Any]] = []
        
        # Styling
        self.default_radius = config.get("default_radius", 8)
        self.risk_colors = {
            "low": "#28a745",
            "medium": "#ffc107", 
            "high": "#fd7e14",
            "critical": "#dc3545"
        }
    
    async def initialize(self):
        """Initialize the port chokepoints layer"""
        try:
            await self._load_ports_data()
            self.is_initialized = True
            logger.info("Port chokepoints layer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize port chokepoints layer: {str(e)}")
            raise
    
    async def _load_ports_data(self):
        """Load port chokepoints data from file"""
        try:
            with open(self.ports_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                if data.get("type") == "FeatureCollection":
                    self.ports_data = data.get("features", [])
                else:
                    self.ports_data = [data] if data else []
            
            logger.info(f"Loaded {len(self.ports_data)} port chokepoints")
            
        except FileNotFoundError:
            logger.warning(f"Ports file not found: {self.ports_file}. Using default data.")
            await self._create_default_ports_data()
        except Exception as e:
            logger.error(f"Failed to load ports data: {str(e)}")
            await self._create_default_ports_data()
    
    async def _create_default_ports_data(self):
        """Create default port chokepoints data"""
        default_ports = [
            {
                "id": "strait_of_malacca",
                "name": "Strait of Malacca",
                "lat": 1.4,
                "lon": 103.8,
                "type": "strait",
                "risk_level": "high",
                "importance": "critical",
                "description": "Major shipping route between Indian and Pacific Oceans"
            },
            {
                "id": "suez_canal",
                "name": "Suez Canal",
                "lat": 30.0,
                "lon": 32.3,
                "type": "canal",
                "risk_level": "medium",
                "importance": "critical",
                "description": "Connects Mediterranean and Red Seas"
            },
            {
                "id": "panama_canal",
                "name": "Panama Canal",
                "lat": 9.0,
                "lon": -79.5,
                "type": "canal",
                "risk_level": "low",
                "importance": "critical",
                "description": "Connects Atlantic and Pacific Oceans"
            },
            {
                "id": "strait_of_hormuz",
                "name": "Strait of Hormuz",
                "lat": 26.6,
                "lon": 56.2,
                "type": "strait",
                "risk_level": "critical",
                "importance": "critical",
                "description": "Oil shipping chokepoint in Persian Gulf"
            },
            {
                "id": "bab_el_mandeb",
                "name": "Bab el-Mandeb",
                "lat": 12.6,
                "lon": 43.3,
                "type": "strait",
                "risk_level": "high",
                "importance": "high",
                "description": "Connects Red Sea to Gulf of Aden"
            },
            {
                "id": "strait_of_gibraltar",
                "name": "Strait of Gibraltar",
                "lat": 35.9,
                "lon": -5.3,
                "type": "strait",
                "risk_level": "low",
                "importance": "high",
                "description": "Connects Mediterranean to Atlantic"
            },
            {
                "id": "bosphorus",
                "name": "Bosphorus Strait",
                "lat": 41.0,
                "lon": 29.0,
                "type": "strait",
                "risk_level": "medium",
                "importance": "high",
                "description": "Connects Black Sea to Mediterranean"
            },
            {
                "id": "english_channel",
                "name": "English Channel",
                "lat": 50.0,
                "lon": -1.0,
                "type": "strait",
                "risk_level": "low",
                "importance": "high",
                "description": "Connects North Sea to Atlantic"
            }
        ]
        
        self.ports_data = default_ports
        logger.info("Created default port chokepoints data")
    
    async def update_data(self, **kwargs) -> List[GeoFeature]:
        """Update port chokepoints data"""
        features = []
        
        for port_data in self.ports_data:
            try:
                feature = self._create_port_feature(port_data)
                if feature:
                    features.append(feature)
            except Exception as e:
                logger.error(f"Error creating port feature: {str(e)}")
                continue
        
        self.features = features
        self.last_update = datetime.utcnow()
        return features
    
    def _create_port_feature(self, port_data: Dict[str, Any]) -> Optional[GeoFeature]:
        """Create a port feature from data"""
        try:
            # Extract coordinates
            if "geometry" in port_data and port_data["geometry"]["type"] == "Point":
                coords = port_data["geometry"]["coordinates"]
                lon, lat = coords[0], coords[1]
            elif "lat" in port_data and "lon" in port_data:
                lat = port_data["lat"]
                lon = port_data["lon"]
            else:
                return None
            
            # Extract properties
            properties = port_data.get("properties", {})
            port_id = properties.get("id", port_data.get("id", f"port_{lat}_{lon}"))
            name = properties.get("name", port_data.get("name", "Unknown Port"))
            port_type = properties.get("type", port_data.get("type", "port"))
            risk_level = properties.get("risk_level", port_data.get("risk_level", "medium"))
            importance = properties.get("importance", port_data.get("importance", "medium"))
            description = properties.get("description", port_data.get("description", ""))
            
            # Create feature
            feature = self._create_point_feature(
                id=port_id,
                lat=lat,
                lon=lon,
                properties={
                    "name": name,
                    "type": port_type,
                    "risk_level": risk_level,
                    "importance": importance,
                    "description": description,
                    "port_type": "chokepoint"
                },
                style={
                    "radius": self._get_port_radius(importance),
                    "color": self._get_port_color(risk_level),
                    "opacity": 0.8,
                    "stroke_color": "#000000",
                    "stroke_width": 1
                }
            )
            
            return feature
            
        except Exception as e:
            logger.error(f"Error creating port feature: {str(e)}")
            return None
    
    def _get_port_radius(self, importance: str) -> int:
        """Get port radius based on importance"""
        radius_map = {
            "critical": 12,
            "high": 10,
            "medium": 8,
            "low": 6
        }
        return radius_map.get(importance.lower(), self.default_radius)
    
    def _get_port_color(self, risk_level: str) -> str:
        """Get port color based on risk level"""
        return self.risk_colors.get(risk_level.lower(), "#6c757d")
    
    def get_features(self, bounds: Optional[GeoBounds] = None, filter_params: Optional[Dict[str, Any]] = None) -> List[GeoFeature]:
        """Get port features within bounds"""
        features = self.features.copy()
        
        # Apply bounds filter
        if bounds:
            features = self._filter_features_by_bounds(features, bounds)
        
        # Apply additional filters
        if filter_params:
            features = self._apply_filters(features, filter_params)
        
        return features
    
    def get_ports_by_risk_level(self, risk_level: str) -> List[GeoFeature]:
        """Get ports by risk level"""
        return [f for f in self.features if f.properties.get("risk_level") == risk_level]
    
    def get_ports_by_importance(self, importance: str) -> List[GeoFeature]:
        """Get ports by importance level"""
        return [f for f in self.features if f.properties.get("importance") == importance]
    
    def get_port_statistics(self) -> Dict[str, Any]:
        """Get port statistics"""
        if not self.features:
            return {"total_ports": 0}
        
        # Count by risk level
        risk_counts = {}
        importance_counts = {}
        type_counts = {}
        
        for feature in self.features:
            risk_level = feature.properties.get("risk_level", "unknown")
            importance = feature.properties.get("importance", "unknown")
            port_type = feature.properties.get("type", "unknown")
            
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
            importance_counts[importance] = importance_counts.get(importance, 0) + 1
            type_counts[port_type] = type_counts.get(port_type, 0) + 1
        
        return {
            "total_ports": len(self.features),
            "risk_levels": risk_counts,
            "importance_levels": importance_counts,
            "port_types": type_counts
        }
    
    def find_nearest_port(self, lat: float, lon: float, max_distance: float = 100.0) -> Optional[GeoFeature]:
        """Find nearest port within distance"""
        from geopy.distance import geodesic
        
        nearest_port = None
        min_distance = float('inf')
        
        for feature in self.features:
            if feature.geometry["type"] == "Point":
                coords = feature.geometry["coordinates"]
                port_lat, port_lon = coords[1], coords[0]
                
                distance = geodesic((lat, lon), (port_lat, port_lon)).kilometers
                
                if distance <= max_distance and distance < min_distance:
                    min_distance = distance
                    nearest_port = feature
        
        return nearest_port
    
    def export_ports_data(self, format: str = "geojson") -> str:
        """Export ports data in specified format"""
        if format == "geojson":
            features = []
            for feature in self.features:
                features.append({
                    "type": "Feature",
                    "id": feature.id,
                    "geometry": feature.geometry,
                    "properties": feature.properties
                })
            
            geojson = {
                "type": "FeatureCollection",
                "features": features
            }
            
            return json.dumps(geojson, indent=2)
        
        return ""
