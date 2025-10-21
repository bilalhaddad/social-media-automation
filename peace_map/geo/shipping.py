"""
Shipping lanes layer for Peace Map platform
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseGeoLayer, GeoFeature, GeoBounds, LayerType, LayerStyle

logger = logging.getLogger(__name__)


class ShippingLanesLayer(BaseGeoLayer):
    """Shipping lanes layer showing major maritime routes"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("shipping_lanes", config)
        self.layer_config.type = LayerType.LINES
        self.layer_config.style = LayerStyle.STROKE
        
        # Shipping lanes data
        self.lanes_file = config.get("lanes_file", "data/shipping_lanes.geojson")
        self.lanes_data: List[Dict[str, Any]] = []
        
        # Styling
        self.default_width = config.get("default_width", 3)
        self.traffic_colors = {
            "high": "#ff0000",      # Red for high traffic
            "medium": "#ffa500",    # Orange for medium traffic
            "low": "#00ff00"        # Green for low traffic
        }
    
    async def initialize(self):
        """Initialize the shipping lanes layer"""
        try:
            await self._load_lanes_data()
            self.is_initialized = True
            logger.info("Shipping lanes layer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize shipping lanes layer: {str(e)}")
            raise
    
    async def _load_lanes_data(self):
        """Load shipping lanes data from file"""
        try:
            with open(self.lanes_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                if data.get("type") == "FeatureCollection":
                    self.lanes_data = data.get("features", [])
                else:
                    self.lanes_data = [data] if data else []
            
            logger.info(f"Loaded {len(self.lanes_data)} shipping lanes")
            
        except FileNotFoundError:
            logger.warning(f"Shipping lanes file not found: {self.lanes_file}. Using default data.")
            await self._create_default_lanes_data()
        except Exception as e:
            logger.error(f"Failed to load shipping lanes data: {str(e)}")
            await self._create_default_lanes_data()
    
    async def _create_default_lanes_data(self):
        """Create default shipping lanes data"""
        default_lanes = [
            {
                "id": "trans_pacific",
                "name": "Trans-Pacific Route",
                "coordinates": [
                    [139.7, 35.7],  # Tokyo
                    [121.5, 25.0],   # Taiwan Strait
                    [103.8, 1.4],    # Strait of Malacca
                    [100.0, 13.7],   # Gulf of Thailand
                    [106.6, 10.8]    # Ho Chi Minh City
                ],
                "traffic_level": "high",
                "route_type": "container",
                "description": "Major container shipping route"
            },
            {
                "id": "europe_asia",
                "name": "Europe-Asia Route",
                "coordinates": [
                    [2.3, 48.9],     # Rotterdam
                    [0.0, 50.0],     # English Channel
                    [-5.3, 35.9],    # Strait of Gibraltar
                    [32.3, 30.0],    # Suez Canal
                    [56.2, 26.6],    # Strait of Hormuz
                    [103.8, 1.4]     # Strait of Malacca
                ],
                "traffic_level": "high",
                "route_type": "container",
                "description": "Suez Canal route to Asia"
            },
            {
                "id": "trans_atlantic",
                "name": "Trans-Atlantic Route",
                "coordinates": [
                    [-74.0, 40.7],   # New York
                    [-79.5, 9.0],    # Panama Canal
                    [-122.4, 37.8],  # San Francisco
                    [139.7, 35.7]    # Tokyo
                ],
                "traffic_level": "medium",
                "route_type": "container",
                "description": "Panama Canal route"
            },
            {
                "id": "oil_route_persian_gulf",
                "name": "Persian Gulf Oil Route",
                "coordinates": [
                    [56.2, 26.6],    # Strait of Hormuz
                    [43.3, 12.6],    # Bab el-Mandeb
                    [32.3, 30.0],    # Suez Canal
                    [0.0, 50.0]       # English Channel
                ],
                "traffic_level": "high",
                "route_type": "oil",
                "description": "Oil shipping from Persian Gulf"
            },
            {
                "id": "north_sea_route",
                "name": "Northern Sea Route",
                "coordinates": [
                    [29.0, 41.0],    # Bosphorus
                    [37.6, 55.8],    # Moscow
                    [37.6, 55.8],    # Arctic route
                    [139.7, 35.7]    # Tokyo
                ],
                "traffic_level": "low",
                "route_type": "general",
                "description": "Arctic shipping route"
            }
        ]
        
        self.lanes_data = default_lanes
        logger.info("Created default shipping lanes data")
    
    async def update_data(self, **kwargs) -> List[GeoFeature]:
        """Update shipping lanes data"""
        features = []
        
        for lane_data in self.lanes_data:
            try:
                feature = self._create_lane_feature(lane_data)
                if feature:
                    features.append(feature)
            except Exception as e:
                logger.error(f"Error creating lane feature: {str(e)}")
                continue
        
        self.features = features
        self.last_update = datetime.utcnow()
        return features
    
    def _create_lane_feature(self, lane_data: Dict[str, Any]) -> Optional[GeoFeature]:
        """Create a shipping lane feature from data"""
        try:
            # Extract coordinates
            if "geometry" in lane_data and lane_data["geometry"]["type"] == "LineString":
                coordinates = lane_data["geometry"]["coordinates"]
            elif "coordinates" in lane_data:
                coordinates = lane_data["coordinates"]
            else:
                return None
            
            # Extract properties
            properties = lane_data.get("properties", {})
            lane_id = properties.get("id", lane_data.get("id", f"lane_{len(self.features)}"))
            name = properties.get("name", lane_data.get("name", "Unknown Lane"))
            traffic_level = properties.get("traffic_level", lane_data.get("traffic_level", "medium"))
            route_type = properties.get("route_type", lane_data.get("route_type", "general"))
            description = properties.get("description", lane_data.get("description", ""))
            
            # Create feature
            feature = self._create_line_feature(
                id=lane_id,
                coordinates=coordinates,
                properties={
                    "name": name,
                    "traffic_level": traffic_level,
                    "route_type": route_type,
                    "description": description,
                    "lane_type": "shipping"
                },
                style={
                    "color": self._get_lane_color(traffic_level),
                    "width": self._get_lane_width(traffic_level),
                    "opacity": 0.7,
                    "dash_array": self._get_dash_pattern(route_type)
                }
            )
            
            return feature
            
        except Exception as e:
            logger.error(f"Error creating lane feature: {str(e)}")
            return None
    
    def _get_lane_color(self, traffic_level: str) -> str:
        """Get lane color based on traffic level"""
        return self.traffic_colors.get(traffic_level.lower(), "#0000ff")
    
    def _get_lane_width(self, traffic_level: str) -> int:
        """Get lane width based on traffic level"""
        width_map = {
            "high": 5,
            "medium": 3,
            "low": 2
        }
        return width_map.get(traffic_level.lower(), self.default_width)
    
    def _get_dash_pattern(self, route_type: str) -> List[int]:
        """Get dash pattern based on route type"""
        patterns = {
            "container": [],  # Solid line
            "oil": [5, 5],   # Dashed line
            "general": [10, 5]  # Dotted line
        }
        return patterns.get(route_type.lower(), [])
    
    def get_features(self, bounds: Optional[GeoBounds] = None, filter_params: Optional[Dict[str, Any]] = None) -> List[GeoFeature]:
        """Get shipping lane features within bounds"""
        features = self.features.copy()
        
        # Apply bounds filter
        if bounds:
            features = self._filter_features_by_bounds(features, bounds)
        
        # Apply additional filters
        if filter_params:
            features = self._apply_filters(features, filter_params)
        
        return features
    
    def get_lanes_by_traffic_level(self, traffic_level: str) -> List[GeoFeature]:
        """Get lanes by traffic level"""
        return [f for f in self.features if f.properties.get("traffic_level") == traffic_level]
    
    def get_lanes_by_route_type(self, route_type: str) -> List[GeoFeature]:
        """Get lanes by route type"""
        return [f for f in self.features if f.properties.get("route_type") == route_type]
    
    def get_lane_statistics(self) -> Dict[str, Any]:
        """Get lane statistics"""
        if not self.features:
            return {"total_lanes": 0}
        
        # Count by traffic level
        traffic_counts = {}
        route_type_counts = {}
        total_length = 0.0
        
        for feature in self.features:
            traffic_level = feature.properties.get("traffic_level", "unknown")
            route_type = feature.properties.get("route_type", "unknown")
            
            traffic_counts[traffic_level] = traffic_counts.get(traffic_level, 0) + 1
            route_type_counts[route_type] = route_type_counts.get(route_type, 0) + 1
            
            # Calculate approximate length
            if feature.geometry["type"] == "LineString":
                coords = feature.geometry["coordinates"]
                if len(coords) >= 2:
                    # Simple distance calculation (not accurate for long distances)
                    from geopy.distance import geodesic
                    length = 0
                    for i in range(len(coords) - 1):
                        lat1, lon1 = coords[i][1], coords[i][0]
                        lat2, lon2 = coords[i+1][1], coords[i+1][0]
                        length += geodesic((lat1, lon1), (lat2, lon2)).kilometers
                    total_length += length
        
        return {
            "total_lanes": len(self.features),
            "traffic_levels": traffic_counts,
            "route_types": route_type_counts,
            "total_length_km": round(total_length, 2)
        }
    
    def find_lanes_through_region(self, bounds: GeoBounds) -> List[GeoFeature]:
        """Find lanes that pass through a specific region"""
        intersecting_lanes = []
        
        for feature in self.features:
            if self._lane_intersects_bounds(feature, bounds):
                intersecting_lanes.append(feature)
        
        return intersecting_lanes
    
    def _lane_intersects_bounds(self, feature: GeoFeature, bounds: GeoBounds) -> bool:
        """Check if a lane intersects with bounds"""
        if feature.geometry["type"] != "LineString":
            return False
        
        coords = feature.geometry["coordinates"]
        for coord in coords:
            lon, lat = coord[0], coord[1]
            if bounds.contains(lat, lon):
                return True
        
        return False
    
    def export_lanes_data(self, format: str = "geojson") -> str:
        """Export lanes data in specified format"""
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
