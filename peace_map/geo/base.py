"""
Base geospatial layer for Peace Map platform
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LayerType(str, Enum):
    """Types of geo layers"""
    HEATMAP = "heatmap"
    POINTS = "points"
    LINES = "lines"
    POLYGONS = "polygons"
    RASTER = "raster"


class LayerStyle(str, Enum):
    """Layer styling options"""
    FILL = "fill"
    STROKE = "stroke"
    CIRCLE = "circle"
    ICON = "icon"
    HEATMAP = "heatmap"


@dataclass
class GeoBounds:
    """Geographic bounds"""
    north: float
    south: float
    east: float
    west: float
    
    def contains(self, lat: float, lon: float) -> bool:
        """Check if point is within bounds"""
        return (self.south <= lat <= self.north and 
                self.west <= lon <= self.east)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "north": self.north,
            "south": self.south,
            "east": self.east,
            "west": self.west
        }


@dataclass
class GeoFeature:
    """Geographic feature"""
    id: str
    geometry: Dict[str, Any]  # GeoJSON geometry
    properties: Dict[str, Any]
    style: Optional[Dict[str, Any]] = None


@dataclass
class LayerConfig:
    """Layer configuration"""
    name: str
    type: LayerType
    style: LayerStyle
    visible: bool = True
    opacity: float = 1.0
    z_index: int = 0
    bounds: Optional[GeoBounds] = None
    filter: Optional[Dict[str, Any]] = None


class BaseGeoLayer(ABC):
    """Abstract base class for geo layers"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.layer_config = LayerConfig(
            name=name,
            type=LayerType.POINTS,  # Default type
            style=LayerStyle.CIRCLE,
            visible=config.get("visible", True),
            opacity=config.get("opacity", 1.0),
            z_index=config.get("z_index", 0)
        )
        self.features: List[GeoFeature] = []
        self.last_update: Optional[datetime] = None
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self):
        """Initialize the layer"""
        pass
    
    @abstractmethod
    async def update_data(self, **kwargs) -> List[GeoFeature]:
        """
        Update layer data
        
        Args:
            **kwargs: Update parameters
            
        Returns:
            List of updated features
        """
        pass
    
    @abstractmethod
    def get_features(self, bounds: Optional[GeoBounds] = None, filter_params: Optional[Dict[str, Any]] = None) -> List[GeoFeature]:
        """
        Get features within bounds and filter
        
        Args:
            bounds: Geographic bounds to filter by
            filter_params: Additional filter parameters
            
        Returns:
            List of filtered features
        """
        pass
    
    def get_layer_info(self) -> Dict[str, Any]:
        """Get layer information"""
        return {
            "name": self.name,
            "type": self.layer_config.type.value,
            "style": self.layer_config.style.value,
            "visible": self.layer_config.visible,
            "opacity": self.layer_config.opacity,
            "z_index": self.layer_config.z_index,
            "feature_count": len(self.features),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "is_initialized": self.is_initialized
        }
    
    def set_visibility(self, visible: bool):
        """Set layer visibility"""
        self.layer_config.visible = visible
    
    def set_opacity(self, opacity: float):
        """Set layer opacity"""
        self.layer_config.opacity = max(0.0, min(1.0, opacity))
    
    def set_z_index(self, z_index: int):
        """Set layer z-index"""
        self.layer_config.z_index = z_index
    
    def _create_point_feature(self, id: str, lat: float, lon: float, properties: Dict[str, Any], style: Optional[Dict[str, Any]] = None) -> GeoFeature:
        """Create a point feature"""
        geometry = {
            "type": "Point",
            "coordinates": [lon, lat]
        }
        
        return GeoFeature(
            id=id,
            geometry=geometry,
            properties=properties,
            style=style
        )
    
    def _create_line_feature(self, id: str, coordinates: List[List[float]], properties: Dict[str, Any], style: Optional[Dict[str, Any]] = None) -> GeoFeature:
        """Create a line feature"""
        geometry = {
            "type": "LineString",
            "coordinates": coordinates
        }
        
        return GeoFeature(
            id=id,
            geometry=geometry,
            properties=properties,
            style=style
        )
    
    def _create_polygon_feature(self, id: str, coordinates: List[List[List[float]]], properties: Dict[str, Any], style: Optional[Dict[str, Any]] = None) -> GeoFeature:
        """Create a polygon feature"""
        geometry = {
            "type": "Polygon",
            "coordinates": coordinates
        }
        
        return GeoFeature(
            id=id,
            geometry=geometry,
            properties=properties,
            style=style
        )
    
    def _filter_features_by_bounds(self, features: List[GeoFeature], bounds: GeoBounds) -> List[GeoFeature]:
        """Filter features by geographic bounds"""
        filtered = []
        
        for feature in features:
            if self._feature_in_bounds(feature, bounds):
                filtered.append(feature)
        
        return filtered
    
    def _feature_in_bounds(self, feature: GeoFeature, bounds: GeoBounds) -> bool:
        """Check if feature is within bounds"""
        geometry = feature.geometry
        
        if geometry["type"] == "Point":
            coords = geometry["coordinates"]
            return bounds.contains(coords[1], coords[0])  # lat, lon
        
        elif geometry["type"] == "LineString":
            coords = geometry["coordinates"]
            return any(bounds.contains(coord[1], coord[0]) for coord in coords)
        
        elif geometry["type"] == "Polygon":
            coords = geometry["coordinates"][0]  # Exterior ring
            return any(bounds.contains(coord[1], coord[0]) for coord in coords)
        
        return True  # Default to include if type unknown
    
    def _apply_filters(self, features: List[GeoFeature], filter_params: Dict[str, Any]) -> List[GeoFeature]:
        """Apply filters to features"""
        if not filter_params:
            return features
        
        filtered = []
        
        for feature in features:
            if self._feature_matches_filters(feature, filter_params):
                filtered.append(feature)
        
        return filtered
    
    def _feature_matches_filters(self, feature: GeoFeature, filters: Dict[str, Any]) -> bool:
        """Check if feature matches filter criteria"""
        properties = feature.properties
        
        for key, value in filters.items():
            if key not in properties:
                return False
            
            if isinstance(value, dict):
                # Range filter
                if "min" in value and properties[key] < value["min"]:
                    return False
                if "max" in value and properties[key] > value["max"]:
                    return False
            elif isinstance(value, list):
                # List filter
                if properties[key] not in value:
                    return False
            else:
                # Exact match
                if properties[key] != value:
                    return False
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get layer statistics"""
        if not self.features:
            return {"total_features": 0}
        
        # Count by type
        type_counts = {}
        for feature in self.features:
            feature_type = feature.properties.get("type", "unknown")
            type_counts[feature_type] = type_counts.get(feature_type, 0) + 1
        
        return {
            "total_features": len(self.features),
            "type_counts": type_counts,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
