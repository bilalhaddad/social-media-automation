"""
Suppliers layer for Peace Map platform
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseGeoLayer, GeoFeature, GeoBounds, LayerType, LayerStyle

logger = logging.getLogger(__name__)


class SuppliersLayer(BaseGeoLayer):
    """Suppliers layer showing supplier locations and risk levels"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("suppliers", config)
        self.layer_config.type = LayerType.POINTS
        self.layer_config.style = LayerStyle.CIRCLE
        
        # Supplier styling
        self.risk_colors = {
            "low": "#28a745",      # Green
            "medium": "#ffc107",   # Yellow
            "high": "#fd7e14",     # Orange
            "critical": "#dc3545"  # Red
        }
        
        self.risk_sizes = {
            "low": 6,
            "medium": 8,
            "high": 10,
            "critical": 12
        }
        
        # Supplier data
        self.suppliers: List[Dict[str, Any]] = []
        self.max_suppliers = config.get("max_suppliers", 500)
    
    async def initialize(self):
        """Initialize the suppliers layer"""
        try:
            self.is_initialized = True
            logger.info("Suppliers layer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize suppliers layer: {str(e)}")
            raise
    
    async def update_data(self, suppliers: List[Dict[str, Any]] = None, **kwargs) -> List[GeoFeature]:
        """Update suppliers data"""
        if suppliers is not None:
            self.suppliers = suppliers
        
        # Limit number of suppliers
        if len(self.suppliers) > self.max_suppliers:
            # Sort by risk level and take top suppliers
            self.suppliers.sort(key=lambda s: self._get_risk_priority(s.get("risk_level", "low")))
            self.suppliers = self.suppliers[:self.max_suppliers]
        
        # Generate features
        features = []
        for supplier in self.suppliers:
            try:
                feature = self._create_supplier_feature(supplier)
                if feature:
                    features.append(feature)
            except Exception as e:
                logger.error(f"Error creating supplier feature: {str(e)}")
                continue
        
        self.features = features
        self.last_update = datetime.utcnow()
        return features
    
    def _create_supplier_feature(self, supplier: Dict[str, Any]) -> Optional[GeoFeature]:
        """Create a feature from a supplier"""
        try:
            # Check if supplier has location
            if not supplier.get("latitude") or not supplier.get("longitude"):
                return None
            
            lat = float(supplier["latitude"])
            lon = float(supplier["longitude"])
            
            # Get risk level
            risk_level = supplier.get("risk_level", "low")
            risk_score = supplier.get("risk_score", 0.0)
            
            # Get styling based on risk
            color = self._get_supplier_color(risk_level)
            size = self._get_supplier_size(risk_level)
            
            # Create properties
            properties = {
                "supplier_id": supplier.get("id", ""),
                "name": supplier.get("name", "Unknown Supplier"),
                "country": supplier.get("country", ""),
                "region": supplier.get("region", ""),
                "city": supplier.get("city", ""),
                "industry": supplier.get("industry", ""),
                "risk_level": risk_level,
                "risk_score": risk_score,
                "supplier_type": "supplier",
                "contact_email": supplier.get("contact_email", ""),
                "contact_phone": supplier.get("contact_phone", ""),
                "last_updated": supplier.get("last_updated", datetime.utcnow().isoformat())
            }
            
            # Add additional supplier data
            if "products" in supplier:
                properties["products"] = supplier["products"]
            if "certifications" in supplier:
                properties["certifications"] = supplier["certifications"]
            if "supply_chain_tier" in supplier:
                properties["supply_chain_tier"] = supplier["supply_chain_tier"]
            
            # Create feature
            feature = self._create_point_feature(
                id=supplier.get("id", f"supplier_{lat}_{lon}"),
                lat=lat,
                lon=lon,
                properties=properties,
                style={
                    "radius": size,
                    "color": color,
                    "opacity": 0.8,
                    "stroke_color": "#000000",
                    "stroke_width": 1
                }
            )
            
            return feature
            
        except Exception as e:
            logger.error(f"Error creating supplier feature: {str(e)}")
            return None
    
    def _get_supplier_color(self, risk_level: str) -> str:
        """Get color for supplier risk level"""
        return self.risk_colors.get(risk_level.lower(), "#6c757d")
    
    def _get_supplier_size(self, risk_level: str) -> int:
        """Get size for supplier risk level"""
        return self.risk_sizes.get(risk_level.lower(), 6)
    
    def _get_risk_priority(self, risk_level: str) -> int:
        """Get priority for sorting by risk level"""
        priorities = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        return priorities.get(risk_level.lower(), 0)
    
    def get_features(self, bounds: Optional[GeoBounds] = None, filter_params: Optional[Dict[str, Any]] = None) -> List[GeoFeature]:
        """Get supplier features within bounds"""
        features = self.features.copy()
        
        # Apply bounds filter
        if bounds:
            features = self._filter_features_by_bounds(features, bounds)
        
        # Apply additional filters
        if filter_params:
            features = self._apply_filters(features, filter_params)
        
        return features
    
    def get_suppliers_by_risk_level(self, risk_level: str) -> List[GeoFeature]:
        """Get suppliers by risk level"""
        return [f for f in self.features if f.properties.get("risk_level") == risk_level]
    
    def get_suppliers_by_industry(self, industry: str) -> List[GeoFeature]:
        """Get suppliers by industry"""
        return [f for f in self.features if f.properties.get("industry") == industry]
    
    def get_suppliers_by_country(self, country: str) -> List[GeoFeature]:
        """Get suppliers by country"""
        return [f for f in self.features if f.properties.get("country") == country]
    
    def get_suppliers_by_risk_score_range(self, min_score: float, max_score: float) -> List[GeoFeature]:
        """Get suppliers by risk score range"""
        filtered = []
        
        for feature in self.features:
            risk_score = feature.properties.get("risk_score", 0.0)
            if min_score <= risk_score <= max_score:
                filtered.append(feature)
        
        return filtered
    
    def get_supplier_statistics(self) -> Dict[str, Any]:
        """Get supplier statistics"""
        if not self.features:
            return {"total_suppliers": 0}
        
        # Count by risk level
        risk_counts = {}
        industry_counts = {}
        country_counts = {}
        tier_counts = {}
        
        total_risk_score = 0.0
        high_risk_count = 0
        
        for feature in self.features:
            risk_level = feature.properties.get("risk_level", "unknown")
            industry = feature.properties.get("industry", "unknown")
            country = feature.properties.get("country", "unknown")
            tier = feature.properties.get("supply_chain_tier", "unknown")
            risk_score = feature.properties.get("risk_score", 0.0)
            
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
            country_counts[country] = country_counts.get(country, 0) + 1
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            total_risk_score += risk_score
            
            if risk_level in ["high", "critical"]:
                high_risk_count += 1
        
        avg_risk_score = total_risk_score / len(self.features) if self.features else 0.0
        
        return {
            "total_suppliers": len(self.features),
            "risk_levels": risk_counts,
            "industries": industry_counts,
            "countries": country_counts,
            "supply_chain_tiers": tier_counts,
            "average_risk_score": round(avg_risk_score, 2),
            "high_risk_count": high_risk_count,
            "high_risk_percentage": round((high_risk_count / len(self.features)) * 100, 1) if self.features else 0
        }
    
    def get_suppliers_at_risk(self, risk_threshold: float = 70.0) -> List[GeoFeature]:
        """Get suppliers with risk score above threshold"""
        return [f for f in self.features if f.properties.get("risk_score", 0.0) >= risk_threshold]
    
    def get_suppliers_in_region(self, bounds: GeoBounds) -> List[GeoFeature]:
        """Get suppliers in a specific region"""
        return self._filter_features_by_bounds(self.features, bounds)
    
    def get_supplier_risk_distribution(self) -> Dict[str, Any]:
        """Get risk distribution of suppliers"""
        if not self.features:
            return {"distribution": {}, "total": 0}
        
        # Group by risk score ranges
        ranges = {
            "0-20": 0,
            "21-40": 0,
            "41-60": 0,
            "61-80": 0,
            "81-100": 0
        }
        
        for feature in self.features:
            risk_score = feature.properties.get("risk_score", 0.0)
            
            if 0 <= risk_score <= 20:
                ranges["0-20"] += 1
            elif 21 <= risk_score <= 40:
                ranges["21-40"] += 1
            elif 41 <= risk_score <= 60:
                ranges["41-60"] += 1
            elif 61 <= risk_score <= 80:
                ranges["61-80"] += 1
            elif 81 <= risk_score <= 100:
                ranges["81-100"] += 1
        
        return {
            "distribution": ranges,
            "total": len(self.features)
        }
    
    def find_nearest_suppliers(self, lat: float, lon: float, max_distance_km: float = 100.0, limit: int = 10) -> List[Dict[str, Any]]:
        """Find nearest suppliers to a location"""
        from geopy.distance import geodesic
        
        suppliers_with_distance = []
        
        for feature in self.features:
            if feature.geometry["type"] == "Point":
                coords = feature.geometry["coordinates"]
                supplier_lat, supplier_lon = coords[1], coords[0]
                
                distance = geodesic((lat, lon), (supplier_lat, supplier_lon)).kilometers
                
                if distance <= max_distance_km:
                    suppliers_with_distance.append({
                        "feature": feature,
                        "distance_km": distance
                    })
        
        # Sort by distance
        suppliers_with_distance.sort(key=lambda x: x["distance_km"])
        
        # Return limited results
        return suppliers_with_distance[:limit]
    
    def get_supplier_clusters(self, bounds: Optional[GeoBounds] = None) -> List[Dict[str, Any]]:
        """Get supplier clusters in a region"""
        features = self.features
        if bounds:
            features = self._filter_features_by_bounds(features, bounds)
        
        if not features:
            return []
        
        # Simple clustering by proximity
        clusters = []
        processed = set()
        
        for i, feature in enumerate(features):
            if i in processed:
                continue
            
            cluster = [feature]
            processed.add(i)
            
            # Find nearby suppliers (within ~25km)
            for j, other_feature in enumerate(features[i+1:], i+1):
                if j in processed:
                    continue
                
                if self._suppliers_are_nearby(feature, other_feature):
                    cluster.append(other_feature)
                    processed.add(j)
            
            if len(cluster) > 1:  # Only include clusters with multiple suppliers
                cluster_center = self._calculate_cluster_center(cluster)
                cluster_risk = self._calculate_cluster_risk(cluster)
                
                clusters.append({
                    "center": cluster_center,
                    "size": len(cluster),
                    "risk_level": cluster_risk,
                    "suppliers": [f.properties["supplier_id"] for f in cluster]
                })
        
        return clusters
    
    def _suppliers_are_nearby(self, feature1: GeoFeature, feature2: GeoFeature, max_distance_km: float = 25.0) -> bool:
        """Check if two suppliers are nearby"""
        try:
            from geopy.distance import geodesic
            
            coords1 = feature1.geometry["coordinates"]
            coords2 = feature2.geometry["coordinates"]
            
            distance = geodesic((coords1[1], coords1[0]), (coords2[1], coords2[0])).kilometers
            return distance <= max_distance_km
        except Exception:
            return False
    
    def _calculate_cluster_center(self, cluster: List[GeoFeature]) -> Dict[str, float]:
        """Calculate center of a supplier cluster"""
        if not cluster:
            return {"lat": 0, "lon": 0}
        
        total_lat = 0
        total_lon = 0
        
        for feature in cluster:
            coords = feature.geometry["coordinates"]
            total_lat += coords[1]
            total_lon += coords[0]
        
        return {
            "lat": total_lat / len(cluster),
            "lon": total_lon / len(cluster)
        }
    
    def _calculate_cluster_risk(self, cluster: List[GeoFeature]) -> str:
        """Calculate overall risk level for a cluster"""
        if not cluster:
            return "low"
        
        # Get risk levels and scores
        risk_levels = [f.properties.get("risk_level", "low") for f in cluster]
        risk_scores = [f.properties.get("risk_score", 0.0) for f in cluster]
        
        # If any critical suppliers, cluster is critical
        if "critical" in risk_levels:
            return "critical"
        
        # If any high risk suppliers, cluster is high
        if "high" in risk_levels:
            return "high"
        
        # Otherwise, use average risk score
        avg_score = sum(risk_scores) / len(risk_scores)
        
        if avg_score >= 80:
            return "critical"
        elif avg_score >= 60:
            return "high"
        elif avg_score >= 40:
            return "medium"
        else:
            return "low"
