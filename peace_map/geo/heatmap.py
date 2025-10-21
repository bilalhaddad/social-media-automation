"""
Risk heatmap layer for Peace Map platform
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
from scipy import ndimage
import json

from .base import BaseGeoLayer, GeoFeature, GeoBounds, LayerType, LayerStyle
from ..ingestion.base import Event

logger = logging.getLogger(__name__)


class RiskHeatmapLayer(BaseGeoLayer):
    """Risk heatmap layer showing regional risk intensity"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("risk_heatmap", config)
        self.layer_config.type = LayerType.HEATMAP
        self.layer_config.style = LayerStyle.HEATMAP
        
        # Heatmap configuration
        self.resolution = config.get("resolution", 0.5)  # degrees
        self.blur_radius = config.get("blur_radius", 2.0)
        self.max_intensity = config.get("max_intensity", 100.0)
        self.color_scheme = config.get("color_scheme", "red")
        
        # Data storage
        self.risk_grid: Optional[np.ndarray] = None
        self.grid_bounds: Optional[GeoBounds] = None
        self.events: List[Event] = []
    
    async def initialize(self):
        """Initialize the heatmap layer"""
        try:
            # Initialize with empty grid
            self._initialize_grid()
            self.is_initialized = True
            logger.info("Risk heatmap layer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize heatmap layer: {str(e)}")
            raise
    
    def _initialize_grid(self, bounds: Optional[GeoBounds] = None):
        """Initialize the risk grid"""
        if bounds is None:
            # Default global bounds
            bounds = GeoBounds(north=85, south=-85, east=180, west=-180)
        
        self.grid_bounds = bounds
        
        # Calculate grid dimensions
        lat_size = int((bounds.north - bounds.south) / self.resolution) + 1
        lon_size = int((bounds.east - bounds.west) / self.resolution) + 1
        
        # Initialize empty grid
        self.risk_grid = np.zeros((lat_size, lon_size))
    
    async def update_data(self, events: List[Event] = None, risk_scores: Dict[str, float] = None, **kwargs) -> List[GeoFeature]:
        """Update heatmap data with events and risk scores"""
        if events is not None:
            self.events = events
        
        if risk_scores is not None:
            await self._update_risk_scores(risk_scores)
        elif self.events:
            await self._calculate_risk_from_events()
        
        # Generate heatmap features
        features = self._generate_heatmap_features()
        
        self.last_update = datetime.utcnow()
        return features
    
    async def _update_risk_scores(self, risk_scores: Dict[str, float]):
        """Update risk scores for regions"""
        # Clear existing grid
        self.risk_grid.fill(0)
        
        for region, score in risk_scores.items():
            # Parse region (could be lat,lon or region name)
            lat, lon = self._parse_region(region)
            if lat is not None and lon is not None:
                self._add_risk_point(lat, lon, score)
    
    async def _calculate_risk_from_events(self):
        """Calculate risk from events"""
        if not self.events:
            return
        
        # Clear existing grid
        self.risk_grid.fill(0)
        
        # Add risk for each event
        for event in self.events:
            if event.location and event.location.get("lat") and event.location.get("lon"):
                lat = event.location["lat"]
                lon = event.location["lon"]
                
                # Calculate risk score based on event
                risk_score = self._calculate_event_risk(event)
                self._add_risk_point(lat, lon, risk_score)
        
        # Apply spatial smoothing
        self._apply_spatial_smoothing()
    
    def _parse_region(self, region: str) -> Tuple[Optional[float], Optional[float]]:
        """Parse region string to lat, lon coordinates"""
        try:
            if "," in region:
                # Format: "lat,lon"
                parts = region.split(",")
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                return lat, lon
            else:
                # Try to parse as region name (simplified)
                # In production, this would use a proper geocoding service
                return None, None
        except (ValueError, IndexError):
            return None, None
    
    def _calculate_event_risk(self, event: Event) -> float:
        """Calculate risk score for an event"""
        base_risk = 1.0
        
        # Adjust based on event category
        category_multipliers = {
            "protest": 0.5,
            "cyber": 0.7,
            "kinetic": 1.5,
            "economic": 0.8,
            "environmental": 0.6,
            "political": 0.9
        }
        
        category = event.category.value if hasattr(event.category, 'value') else str(event.category)
        base_risk *= category_multipliers.get(category, 1.0)
        
        # Adjust based on severity
        severity_multipliers = {
            "low": 0.3,
            "medium": 0.7,
            "high": 1.2,
            "critical": 2.0
        }
        
        severity = event.severity.value if hasattr(event.severity, 'value') else str(event.severity)
        base_risk *= severity_multipliers.get(severity, 1.0)
        
        # Adjust based on confidence
        base_risk *= event.confidence
        
        # Adjust based on sentiment
        if hasattr(event, 'sentiment_score') and event.sentiment_score is not None:
            if event.sentiment_score < 0:
                base_risk *= 1.2  # Negative sentiment increases risk
            elif event.sentiment_score > 0:
                base_risk *= 0.8  # Positive sentiment decreases risk
        
        return min(base_risk, self.max_intensity)
    
    def _add_risk_point(self, lat: float, lon: float, risk_score: float):
        """Add a risk point to the grid"""
        if not self.grid_bounds or self.risk_grid is None:
            return
        
        # Check if point is within bounds
        if not self.grid_bounds.contains(lat, lon):
            return
        
        # Calculate grid indices
        lat_idx = int((lat - self.grid_bounds.south) / self.resolution)
        lon_idx = int((lon - self.grid_bounds.west) / self.resolution)
        
        # Ensure indices are within bounds
        if 0 <= lat_idx < self.risk_grid.shape[0] and 0 <= lon_idx < self.risk_grid.shape[1]:
            self.risk_grid[lat_idx, lon_idx] += risk_score
    
    def _apply_spatial_smoothing(self):
        """Apply spatial smoothing to the risk grid"""
        if self.risk_grid is None:
            return
        
        # Apply Gaussian blur for smoothing
        sigma = self.blur_radius / self.resolution
        self.risk_grid = ndimage.gaussian_filter(self.risk_grid, sigma=sigma)
    
    def _generate_heatmap_features(self) -> List[GeoFeature]:
        """Generate heatmap features from the risk grid"""
        if self.risk_grid is None or self.grid_bounds is None:
            return []
        
        features = []
        
        # Create grid cells as features
        for lat_idx in range(self.risk_grid.shape[0]):
            for lon_idx in range(self.risk_grid.shape[1]):
                risk_value = self.risk_grid[lat_idx, lon_idx]
                
                if risk_value > 0:
                    # Calculate cell bounds
                    lat = self.grid_bounds.south + lat_idx * self.resolution
                    lon = self.grid_bounds.west + lon_idx * self.resolution
                    
                    # Create polygon for grid cell
                    cell_coords = [
                        [lon, lat],
                        [lon + self.resolution, lat],
                        [lon + self.resolution, lat + self.resolution],
                        [lon, lat + self.resolution],
                        [lon, lat]
                    ]
                    
                    # Create feature
                    feature = self._create_polygon_feature(
                        id=f"heatmap_{lat_idx}_{lon_idx}",
                        coordinates=[cell_coords],
                        properties={
                            "risk_score": float(risk_value),
                            "intensity": float(risk_value / self.max_intensity),
                            "type": "risk_heatmap"
                        },
                        style={
                            "fill_color": self._get_heatmap_color(risk_value),
                            "fill_opacity": min(0.8, risk_value / self.max_intensity),
                            "stroke_color": "#000000",
                            "stroke_width": 0
                        }
                    )
                    
                    features.append(feature)
        
        return features
    
    def _get_heatmap_color(self, risk_value: float) -> str:
        """Get color for heatmap based on risk value"""
        intensity = min(risk_value / self.max_intensity, 1.0)
        
        if self.color_scheme == "red":
            # Red color scheme
            red = int(255 * intensity)
            green = int(255 * (1 - intensity))
            blue = 0
            return f"rgb({red},{green},{blue})"
        elif self.color_scheme == "blue":
            # Blue color scheme
            red = 0
            green = int(255 * (1 - intensity))
            blue = int(255 * intensity)
            return f"rgb({red},{green},{blue})"
        else:
            # Default to red
            red = int(255 * intensity)
            green = int(255 * (1 - intensity))
            blue = 0
            return f"rgb({red},{green},{blue})"
    
    def get_features(self, bounds: Optional[GeoBounds] = None, filter_params: Optional[Dict[str, Any]] = None) -> List[GeoFeature]:
        """Get heatmap features within bounds"""
        features = self._generate_heatmap_features()
        
        # Apply bounds filter
        if bounds:
            features = self._filter_features_by_bounds(features, bounds)
        
        # Apply additional filters
        if filter_params:
            features = self._apply_filters(features, filter_params)
        
        return features
    
    def get_risk_at_point(self, lat: float, lon: float) -> float:
        """Get risk value at a specific point"""
        if not self.grid_bounds or self.risk_grid is None:
            return 0.0
        
        if not self.grid_bounds.contains(lat, lon):
            return 0.0
        
        # Calculate grid indices
        lat_idx = int((lat - self.grid_bounds.south) / self.resolution)
        lon_idx = int((lon - self.grid_bounds.west) / self.resolution)
        
        # Check bounds
        if 0 <= lat_idx < self.risk_grid.shape[0] and 0 <= lon_idx < self.risk_grid.shape[1]:
            return float(self.risk_grid[lat_idx, lon_idx])
        
        return 0.0
    
    def get_risk_statistics(self) -> Dict[str, Any]:
        """Get risk statistics"""
        if self.risk_grid is None:
            return {"total_risk": 0, "max_risk": 0, "avg_risk": 0}
        
        total_risk = float(np.sum(self.risk_grid))
        max_risk = float(np.max(self.risk_grid))
        avg_risk = float(np.mean(self.risk_grid[self.risk_grid > 0])) if np.any(self.risk_grid > 0) else 0.0
        
        return {
            "total_risk": total_risk,
            "max_risk": max_risk,
            "avg_risk": avg_risk,
            "grid_size": self.risk_grid.shape,
            "resolution": self.resolution
        }
    
    def export_heatmap_data(self, format: str = "json") -> str:
        """Export heatmap data in specified format"""
        if self.risk_grid is None or self.grid_bounds is None:
            return ""
        
        if format == "json":
            # Export as GeoJSON
            features = self._generate_heatmap_features()
            
            geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "id": feature.id,
                        "geometry": feature.geometry,
                        "properties": feature.properties,
                        "style": feature.style
                    }
                    for feature in features
                ]
            }
            
            return json.dumps(geojson, indent=2)
        
        return ""
