"""
Events layer for Peace Map platform
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base import BaseGeoLayer, GeoFeature, GeoBounds, LayerType, LayerStyle
from ..ingestion.base import Event, EventCategory, EventSeverity

logger = logging.getLogger(__name__)


class EventsLayer(BaseGeoLayer):
    """Events layer showing event locations on the map"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("events", config)
        self.layer_config.type = LayerType.POINTS
        self.layer_config.style = LayerStyle.CIRCLE
        
        # Event styling
        self.category_colors = {
            EventCategory.PROTEST: "#ff6b6b",
            EventCategory.CYBER: "#4ecdc4",
            EventCategory.KINETIC: "#45b7d1",
            EventCategory.ECONOMIC: "#96ceb4",
            EventCategory.ENVIRONMENTAL: "#feca57",
            EventCategory.POLITICAL: "#ff9ff3"
        }
        
        self.severity_sizes = {
            EventSeverity.LOW: 4,
            EventSeverity.MEDIUM: 6,
            EventSeverity.HIGH: 8,
            EventSeverity.CRITICAL: 12
        }
        
        # Event data
        self.events: List[Event] = []
        self.max_events = config.get("max_events", 1000)
        self.time_filter_days = config.get("time_filter_days", 30)
    
    async def initialize(self):
        """Initialize the events layer"""
        try:
            self.is_initialized = True
            logger.info("Events layer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize events layer: {str(e)}")
            raise
    
    async def update_data(self, events: List[Event] = None, **kwargs) -> List[GeoFeature]:
        """Update events data"""
        if events is not None:
            self.events = events
        
        # Filter events by time if specified
        if self.time_filter_days > 0:
            cutoff_date = datetime.utcnow() - timedelta(days=self.time_filter_days)
            self.events = [e for e in self.events if e.published_at >= cutoff_date]
        
        # Limit number of events
        if len(self.events) > self.max_events:
            # Sort by confidence and recency, take top events
            self.events.sort(key=lambda e: (e.confidence, e.published_at), reverse=True)
            self.events = self.events[:self.max_events]
        
        # Generate features
        features = []
        for event in self.events:
            try:
                feature = self._create_event_feature(event)
                if feature:
                    features.append(feature)
            except Exception as e:
                logger.error(f"Error creating event feature: {str(e)}")
                continue
        
        self.features = features
        self.last_update = datetime.utcnow()
        return features
    
    def _create_event_feature(self, event: Event) -> Optional[GeoFeature]:
        """Create a feature from an event"""
        try:
            # Check if event has location
            if not event.location or not event.location.get("lat") or not event.location.get("lon"):
                return None
            
            lat = event.location["lat"]
            lon = event.location["lon"]
            
            # Get styling based on category and severity
            color = self._get_event_color(event.category)
            size = self._get_event_size(event.severity)
            
            # Create properties
            properties = {
                "event_id": event.id,
                "title": event.title,
                "description": event.description,
                "category": event.category.value if hasattr(event.category, 'value') else str(event.category),
                "severity": event.severity.value if hasattr(event.severity, 'value') else str(event.severity),
                "confidence": event.confidence,
                "source": event.source,
                "published_at": event.published_at.isoformat(),
                "country": event.location.get("country", ""),
                "region": event.location.get("region", ""),
                "city": event.location.get("city", ""),
                "event_type": "event"
            }
            
            # Add sentiment if available
            if hasattr(event, 'sentiment_score') and event.sentiment_score is not None:
                properties["sentiment_score"] = event.sentiment_score
            
            # Add tags
            if event.tags:
                properties["tags"] = event.tags
            
            # Create feature
            feature = self._create_point_feature(
                id=event.id,
                lat=lat,
                lon=lon,
                properties=properties,
                style={
                    "radius": size,
                    "color": color,
                    "opacity": min(0.8, event.confidence),
                    "stroke_color": "#000000",
                    "stroke_width": 1
                }
            )
            
            return feature
            
        except Exception as e:
            logger.error(f"Error creating event feature: {str(e)}")
            return None
    
    def _get_event_color(self, category: EventCategory) -> str:
        """Get color for event category"""
        return self.category_colors.get(category, "#6c757d")
    
    def _get_event_size(self, severity: EventSeverity) -> int:
        """Get size for event severity"""
        return self.severity_sizes.get(severity, 6)
    
    def get_features(self, bounds: Optional[GeoBounds] = None, filter_params: Optional[Dict[str, Any]] = None) -> List[GeoFeature]:
        """Get event features within bounds"""
        features = self.features.copy()
        
        # Apply bounds filter
        if bounds:
            features = self._filter_features_by_bounds(features, bounds)
        
        # Apply additional filters
        if filter_params:
            features = self._apply_filters(features, filter_params)
        
        return features
    
    def get_events_by_category(self, category: EventCategory) -> List[GeoFeature]:
        """Get events by category"""
        category_str = category.value if hasattr(category, 'value') else str(category)
        return [f for f in self.features if f.properties.get("category") == category_str]
    
    def get_events_by_severity(self, severity: EventSeverity) -> List[GeoFeature]:
        """Get events by severity"""
        severity_str = severity.value if hasattr(severity, 'value') else str(severity)
        return [f for f in self.features if f.properties.get("severity") == severity_str]
    
    def get_events_by_region(self, country: str = None, region: str = None) -> List[GeoFeature]:
        """Get events by region"""
        filtered = []
        
        for feature in self.features:
            if country and feature.properties.get("country") != country:
                continue
            if region and feature.properties.get("region") != region:
                continue
            filtered.append(feature)
        
        return filtered
    
    def get_events_by_time_range(self, start_date: datetime, end_date: datetime) -> List[GeoFeature]:
        """Get events within time range"""
        filtered = []
        
        for feature in self.features:
            published_at = datetime.fromisoformat(feature.properties.get("published_at", ""))
            if start_date <= published_at <= end_date:
                filtered.append(feature)
        
        return filtered
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get event statistics"""
        if not self.features:
            return {"total_events": 0}
        
        # Count by category
        category_counts = {}
        severity_counts = {}
        source_counts = {}
        country_counts = {}
        
        total_confidence = 0.0
        total_sentiment = 0.0
        sentiment_count = 0
        
        for feature in self.features:
            category = feature.properties.get("category", "unknown")
            severity = feature.properties.get("severity", "unknown")
            source = feature.properties.get("source", "unknown")
            country = feature.properties.get("country", "unknown")
            confidence = feature.properties.get("confidence", 0.0)
            sentiment_score = feature.properties.get("sentiment_score")
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            source_counts[source] = source_counts.get(source, 0) + 1
            country_counts[country] = country_counts.get(country, 0) + 1
            
            total_confidence += confidence
            
            if sentiment_score is not None:
                total_sentiment += sentiment_score
                sentiment_count += 1
        
        avg_confidence = total_confidence / len(self.features) if self.features else 0.0
        avg_sentiment = total_sentiment / sentiment_count if sentiment_count > 0 else 0.0
        
        return {
            "total_events": len(self.features),
            "categories": category_counts,
            "severities": severity_counts,
            "sources": source_counts,
            "countries": country_counts,
            "average_confidence": round(avg_confidence, 3),
            "average_sentiment": round(avg_sentiment, 3),
            "sentiment_count": sentiment_count
        }
    
    def get_events_cluster_analysis(self, bounds: Optional[GeoBounds] = None) -> Dict[str, Any]:
        """Get cluster analysis of events"""
        features = self.features
        if bounds:
            features = self._filter_features_by_bounds(features, bounds)
        
        if not features:
            return {"clusters": [], "total_events": 0}
        
        # Simple clustering by proximity
        clusters = []
        processed = set()
        
        for i, feature in enumerate(features):
            if i in processed:
                continue
            
            cluster = [feature]
            processed.add(i)
            
            # Find nearby events (within ~50km)
            for j, other_feature in enumerate(features[i+1:], i+1):
                if j in processed:
                    continue
                
                if self._events_are_nearby(feature, other_feature):
                    cluster.append(other_feature)
                    processed.add(j)
            
            if len(cluster) > 1:  # Only include clusters with multiple events
                clusters.append({
                    "center": self._calculate_cluster_center(cluster),
                    "size": len(cluster),
                    "events": [f.properties["event_id"] for f in cluster]
                })
        
        return {
            "clusters": clusters,
            "total_events": len(features),
            "clustered_events": sum(c["size"] for c in clusters),
            "cluster_count": len(clusters)
        }
    
    def _events_are_nearby(self, feature1: GeoFeature, feature2: GeoFeature, max_distance_km: float = 50.0) -> bool:
        """Check if two events are nearby"""
        try:
            from geopy.distance import geodesic
            
            coords1 = feature1.geometry["coordinates"]
            coords2 = feature2.geometry["coordinates"]
            
            distance = geodesic((coords1[1], coords1[0]), (coords2[1], coords2[0])).kilometers
            return distance <= max_distance_km
        except Exception:
            return False
    
    def _calculate_cluster_center(self, cluster: List[GeoFeature]) -> Dict[str, float]:
        """Calculate center of a cluster"""
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
