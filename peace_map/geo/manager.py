"""
Geospatial layer manager for Peace Map platform
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseGeoLayer, GeoBounds
from .heatmap import RiskHeatmapLayer
from .ports import PortChokepointsLayer
from .shipping import ShippingLanesLayer
from .events import EventsLayer
from .suppliers import SuppliersLayer

logger = logging.getLogger(__name__)


class GeoLayerManager:
    """Manages all geospatial layers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.layers: Dict[str, BaseGeoLayer] = {}
        self.is_initialized = False
        
        # Initialize layers
        self._initialize_layers()
    
    def _initialize_layers(self):
        """Initialize all configured layers"""
        layer_configs = self.config.get("layers", {})
        
        # Initialize risk heatmap layer
        if layer_configs.get("heatmap", {}).get("enabled", True):
            heatmap_config = layer_configs.get("heatmap", {})
            self.layers["heatmap"] = RiskHeatmapLayer(heatmap_config)
        
        # Initialize port chokepoints layer
        if layer_configs.get("ports", {}).get("enabled", True):
            ports_config = layer_configs.get("ports", {})
            self.layers["ports"] = PortChokepointsLayer(ports_config)
        
        # Initialize shipping lanes layer
        if layer_configs.get("shipping", {}).get("enabled", True):
            shipping_config = layer_configs.get("shipping", {})
            self.layers["shipping"] = ShippingLanesLayer(shipping_config)
        
        # Initialize events layer
        if layer_configs.get("events", {}).get("enabled", True):
            events_config = layer_configs.get("events", {})
            self.layers["events"] = EventsLayer(events_config)
        
        # Initialize suppliers layer
        if layer_configs.get("suppliers", {}).get("enabled", True):
            suppliers_config = layer_configs.get("suppliers", {})
            self.layers["suppliers"] = SuppliersLayer(suppliers_config)
        
        logger.info(f"Initialized {len(self.layers)} geo layers")
    
    async def initialize(self):
        """Initialize all layers"""
        initialization_tasks = []
        
        for layer in self.layers.values():
            initialization_tasks.append(layer.initialize())
        
        if initialization_tasks:
            await asyncio.gather(*initialization_tasks)
            self.is_initialized = True
            logger.info("All geo layers initialized")
    
    async def update_layer(self, layer_name: str, **kwargs) -> List[Any]:
        """Update a specific layer"""
        if layer_name not in self.layers:
            raise ValueError(f"Layer {layer_name} not found")
        
        layer = self.layers[layer_name]
        return await layer.update_data(**kwargs)
    
    async def update_all_layers(self, **kwargs) -> Dict[str, List[Any]]:
        """Update all layers"""
        results = {}
        
        for layer_name, layer in self.layers.items():
            try:
                result = await layer.update_data(**kwargs)
                results[layer_name] = result
            except Exception as e:
                logger.error(f"Error updating layer {layer_name}: {str(e)}")
                results[layer_name] = []
        
        return results
    
    def get_layer(self, layer_name: str) -> Optional[BaseGeoLayer]:
        """Get a specific layer"""
        return self.layers.get(layer_name)
    
    def get_all_layers(self) -> Dict[str, BaseGeoLayer]:
        """Get all layers"""
        return self.layers.copy()
    
    def get_layer_info(self, layer_name: str = None) -> Dict[str, Any]:
        """Get layer information"""
        if layer_name:
            if layer_name in self.layers:
                return self.layers[layer_name].get_layer_info()
            else:
                return {"error": f"Layer {layer_name} not found"}
        else:
            return {
                layer_name: layer.get_layer_info()
                for layer_name, layer in self.layers.items()
            }
    
    def get_features(self, layer_name: str, bounds: Optional[GeoBounds] = None, filter_params: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Get features from a specific layer"""
        if layer_name not in self.layers:
            return []
        
        layer = self.layers[layer_name]
        return layer.get_features(bounds, filter_params)
    
    def get_all_features(self, bounds: Optional[GeoBounds] = None, filter_params: Optional[Dict[str, Any]] = None) -> Dict[str, List[Any]]:
        """Get features from all layers"""
        results = {}
        
        for layer_name, layer in self.layers.items():
            try:
                features = layer.get_features(bounds, filter_params)
                results[layer_name] = features
            except Exception as e:
                logger.error(f"Error getting features from layer {layer_name}: {str(e)}")
                results[layer_name] = []
        
        return results
    
    def set_layer_visibility(self, layer_name: str, visible: bool):
        """Set layer visibility"""
        if layer_name in self.layers:
            self.layers[layer_name].set_visibility(visible)
    
    def set_layer_opacity(self, layer_name: str, opacity: float):
        """Set layer opacity"""
        if layer_name in self.layers:
            self.layers[layer_name].set_opacity(opacity)
    
    def set_layer_z_index(self, layer_name: str, z_index: int):
        """Set layer z-index"""
        if layer_name in self.layers:
            self.layers[layer_name].set_z_index(z_index)
    
    def get_layer_statistics(self, layer_name: str = None) -> Dict[str, Any]:
        """Get layer statistics"""
        if layer_name:
            if layer_name in self.layers:
                return self.layers[layer_name].get_statistics()
            else:
                return {"error": f"Layer {layer_name} not found"}
        else:
            return {
                layer_name: layer.get_statistics()
                for layer_name, layer in self.layers.items()
            }
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """Get overall statistics for all layers"""
        total_features = 0
        layer_stats = {}
        
        for layer_name, layer in self.layers.items():
            stats = layer.get_statistics()
            layer_stats[layer_name] = stats
            total_features += stats.get("total_features", 0)
        
        return {
            "total_layers": len(self.layers),
            "total_features": total_features,
            "layers": layer_stats,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all layers"""
        health_status = {
            "overall_health": "healthy",
            "layers": {},
            "total_layers": len(self.layers),
            "initialized_layers": 0,
            "last_check": datetime.utcnow().isoformat()
        }
        
        for layer_name, layer in self.layers.items():
            try:
                layer_info = layer.get_layer_info()
                health_status["layers"][layer_name] = {
                    "status": "healthy",
                    "initialized": layer_info.get("is_initialized", False),
                    "feature_count": layer_info.get("feature_count", 0),
                    "last_update": layer_info.get("last_update")
                }
                
                if layer_info.get("is_initialized", False):
                    health_status["initialized_layers"] += 1
                    
            except Exception as e:
                health_status["layers"][layer_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_health"] = "degraded"
        
        return health_status
    
    def export_layer_data(self, layer_name: str, format: str = "geojson") -> str:
        """Export layer data in specified format"""
        if layer_name not in self.layers:
            return ""
        
        layer = self.layers[layer_name]
        
        # Check if layer has export method
        if hasattr(layer, f"export_{layer_name}_data"):
            method = getattr(layer, f"export_{layer_name}_data")
            return method(format)
        elif hasattr(layer, "export_data"):
            return layer.export_data(format)
        else:
            # Generic export
            features = layer.get_features()
            
            if format == "geojson":
                import json
                geojson = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "id": feature.id,
                            "geometry": feature.geometry,
                            "properties": feature.properties
                        }
                        for feature in features
                    ]
                }
                return json.dumps(geojson, indent=2)
        
        return ""
    
    def get_layer_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all layers"""
        capabilities = {}
        
        for layer_name, layer in self.layers.items():
            layer_info = layer.get_layer_info()
            capabilities[layer_name] = {
                "type": layer_info.get("type"),
                "style": layer_info.get("style"),
                "supports_filtering": True,
                "supports_bounds": True,
                "supports_export": hasattr(layer, "export_data") or hasattr(layer, f"export_{layer_name}_data"),
                "max_features": getattr(layer, "max_events", getattr(layer, "max_suppliers", None))
            }
        
        return capabilities
    
    def create_custom_layer(self, layer_name: str, layer_type: str, config: Dict[str, Any]) -> bool:
        """Create a custom layer (for future extension)"""
        # This would be used to create custom layers dynamically
        # For now, we only support predefined layer types
        logger.warning(f"Custom layer creation not yet implemented: {layer_name}")
        return False
    
    def remove_layer(self, layer_name: str) -> bool:
        """Remove a layer"""
        if layer_name in self.layers:
            del self.layers[layer_name]
            logger.info(f"Layer {layer_name} removed")
            return True
        return False
    
    async def close(self):
        """Close all layers and cleanup resources"""
        for layer in self.layers.values():
            if hasattr(layer, 'close'):
                await layer.close()
        
        logger.info("Geo layer manager closed")
