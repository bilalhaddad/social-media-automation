"""
Anomaly detection for Peace Map platform
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .base import BaseRiskCalculator, RiskScore, RiskFactor, RiskLevel

logger = logging.getLogger(__name__)


class AnomalyDetector(BaseRiskCalculator):
    """Detects anomalies in risk patterns"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("anomaly", config)
        
        # Anomaly detection parameters
        self.contamination = config.get("contamination", 0.1)  # Expected fraction of outliers
        self.window_size = config.get("window_size", 30)  # Days
        self.min_samples = config.get("min_samples", 10)
        self.z_score_threshold = config.get("z_score_threshold", 2.0)
        
        # Anomaly detection models
        self.isolation_forest = None
        self.scaler = None
        self.is_trained = False
        
        # Historical data for comparison
        self.historical_data = []
        self.baseline_stats = {}
    
    async def initialize(self):
        """Initialize the anomaly detector"""
        try:
            # Initialize models
            self.isolation_forest = IsolationForest(
                contamination=self.contamination,
                random_state=42
            )
            self.scaler = StandardScaler()
            
            self.is_initialized = True
            logger.info("Anomaly detector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize anomaly detector: {str(e)}")
            raise
    
    async def calculate_risk(self, data: Dict[str, Any], **kwargs) -> RiskScore:
        """Calculate anomaly risk score"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Extract data
            current_metrics = data.get("metrics", {})
            region = data.get("region", "unknown")
            time_series_data = data.get("time_series", [])
            
            # Calculate anomaly factors
            factors = []
            
            # Statistical anomaly factor
            stat_anomaly_factor = self._calculate_statistical_anomaly_factor(current_metrics)
            factors.append(stat_anomaly_factor)
            
            # Time series anomaly factor
            if time_series_data:
                ts_anomaly_factor = self._calculate_time_series_anomaly_factor(time_series_data)
                factors.append(ts_anomaly_factor)
            
            # Isolation forest anomaly factor
            if self.is_trained:
                isolation_factor = self._calculate_isolation_anomaly_factor(current_metrics)
                factors.append(isolation_factor)
            
            # Pattern deviation factor
            pattern_factor = self._calculate_pattern_deviation_factor(current_metrics, region)
            factors.append(pattern_factor)
            
            # Calculate weighted score
            overall_score, confidence = self.calculate_weighted_score(factors)
            
            # Normalize score
            overall_score = self.normalize_score(overall_score)
            
            # Get risk level
            risk_level = self.get_risk_level(overall_score)
            
            # Create risk score
            risk_score = RiskScore(
                overall_score=overall_score,
                risk_level=risk_level,
                factors=factors,
                confidence=confidence,
                calculated_at=datetime.utcnow(),
                region=region,
                metadata={
                    "anomaly_detected": overall_score > 70.0,
                    "detection_methods": len(factors),
                    "is_trained": self.is_trained
                }
            )
            
            return risk_score
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            return RiskScore(
                overall_score=0.0,
                risk_level=RiskLevel.LOW,
                factors=[],
                confidence=0.0,
                calculated_at=datetime.utcnow(),
                region=data.get("region", "unknown")
            )
    
    def _calculate_statistical_anomaly_factor(self, metrics: Dict[str, Any]) -> RiskFactor:
        """Calculate statistical anomaly factor using z-score"""
        if not metrics:
            return self._create_risk_factor(
                name="statistical_anomaly",
                value=0.0,
                weight=0.3,
                description="No metrics available",
                source="statistical_analysis",
                confidence=0.0
            )
        
        # Calculate z-scores for each metric
        z_scores = []
        anomaly_scores = []
        
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)) and metric_name in self.baseline_stats:
                baseline_mean = self.baseline_stats[metric_name].get("mean", 0)
                baseline_std = self.baseline_stats[metric_name].get("std", 1)
                
                if baseline_std > 0:
                    z_score = abs((value - baseline_mean) / baseline_std)
                    z_scores.append(z_score)
                    
                    # Convert z-score to anomaly score
                    if z_score > self.z_score_threshold:
                        anomaly_score = min(100.0, z_score * 20)  # Scale to 0-100
                        anomaly_scores.append(anomaly_score)
        
        if not anomaly_scores:
            return self._create_risk_factor(
                name="statistical_anomaly",
                value=0.0,
                weight=0.3,
                description="No significant statistical anomalies",
                source="statistical_analysis",
                confidence=0.5
            )
        
        avg_anomaly_score = np.mean(anomaly_scores)
        
        return self._create_risk_factor(
            name="statistical_anomaly",
            value=avg_anomaly_score,
            weight=0.3,
            description=f"Statistical anomaly score: {avg_anomaly_score:.1f}",
            source="statistical_analysis",
            confidence=0.8
        )
    
    def _calculate_time_series_anomaly_factor(self, time_series: List[Dict[str, Any]]]) -> RiskFactor:
        """Calculate time series anomaly factor"""
        if len(time_series) < self.min_samples:
            return self._create_risk_factor(
                name="time_series_anomaly",
                value=0.0,
                weight=0.25,
                description="Insufficient time series data",
                source="time_series_analysis",
                confidence=0.3
            )
        
        # Extract values and timestamps
        values = []
        timestamps = []
        
        for point in time_series:
            if "value" in point and "timestamp" in point:
                values.append(point["value"])
                timestamps.append(point["timestamp"])
        
        if len(values) < 3:
            return self._create_risk_factor(
                name="time_series_anomaly",
                value=0.0,
                weight=0.25,
                description="Insufficient data points",
                source="time_series_analysis",
                confidence=0.3
            )
        
        # Calculate trend and seasonality
        values_array = np.array(values)
        
        # Simple trend detection
        x = np.arange(len(values_array))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values_array)
        
        # Calculate residuals
        predicted = slope * x + intercept
        residuals = values_array - predicted
        
        # Detect outliers in residuals
        residual_std = np.std(residuals)
        if residual_std > 0:
            z_scores = np.abs(residuals / residual_std)
            outliers = z_scores > self.z_score_threshold
            
            if np.any(outliers):
                anomaly_score = min(100.0, np.max(z_scores) * 15)
            else:
                anomaly_score = 0.0
        else:
            anomaly_score = 0.0
        
        return self._create_risk_factor(
            name="time_series_anomaly",
            value=anomaly_score,
            weight=0.25,
            description=f"Time series anomaly score: {anomaly_score:.1f}",
            source="time_series_analysis",
            confidence=0.7
        )
    
    def _calculate_isolation_anomaly_factor(self, metrics: Dict[str, Any]) -> RiskFactor:
        """Calculate isolation forest anomaly factor"""
        if not self.is_trained or not metrics:
            return self._create_risk_factor(
                name="isolation_anomaly",
                value=0.0,
                weight=0.25,
                description="Model not trained or no metrics",
                source="isolation_forest",
                confidence=0.0
            )
        
        try:
            # Prepare feature vector
            feature_vector = []
            feature_names = []
            
            for name, value in metrics.items():
                if isinstance(value, (int, float)):
                    feature_vector.append(value)
                    feature_names.append(name)
            
            if not feature_vector:
                return self._create_risk_factor(
                    name="isolation_anomaly",
                    value=0.0,
                    weight=0.25,
                    description="No numeric features available",
                    source="isolation_forest",
                    confidence=0.0
                )
            
            # Scale features
            feature_array = np.array(feature_vector).reshape(1, -1)
            scaled_features = self.scaler.transform(feature_array)
            
            # Predict anomaly
            anomaly_score = self.isolation_forest.decision_function(scaled_features)[0]
            is_anomaly = self.isolation_forest.predict(scaled_features)[0]
            
            # Convert to 0-100 scale
            if is_anomaly == -1:  # Anomaly detected
                anomaly_risk = min(100.0, abs(anomaly_score) * 50)
            else:
                anomaly_risk = 0.0
            
            return self._create_risk_factor(
                name="isolation_anomaly",
                value=anomaly_risk,
                weight=0.25,
                description=f"Isolation forest anomaly: {anomaly_risk:.1f}",
                source="isolation_forest",
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Isolation forest prediction failed: {str(e)}")
            return self._create_risk_factor(
                name="isolation_anomaly",
                value=0.0,
                weight=0.25,
                description="Prediction failed",
                source="isolation_forest",
                confidence=0.0
            )
    
    def _calculate_pattern_deviation_factor(self, metrics: Dict[str, Any], region: str) -> RiskFactor:
        """Calculate pattern deviation factor"""
        if not metrics or region not in self.baseline_stats:
            return self._create_risk_factor(
                name="pattern_deviation",
                value=0.0,
                weight=0.2,
                description="No baseline data for region",
                source="pattern_analysis",
                confidence=0.0
            )
        
        # Compare current metrics to regional baseline
        deviations = []
        
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)) and metric_name in self.baseline_stats[region]:
                baseline_mean = self.baseline_stats[region][metric_name].get("mean", 0)
                baseline_std = self.baseline_stats[region][metric_name].get("std", 1)
                
                if baseline_std > 0:
                    deviation = abs((value - baseline_mean) / baseline_std)
                    deviations.append(deviation)
        
        if not deviations:
            return self._create_risk_factor(
                name="pattern_deviation",
                value=0.0,
                weight=0.2,
                description="No comparable metrics",
                source="pattern_analysis",
                confidence=0.0
            )
        
        avg_deviation = np.mean(deviations)
        pattern_risk = min(100.0, avg_deviation * 25)
        
        return self._create_risk_factor(
            name="pattern_deviation",
            value=pattern_risk,
            weight=0.2,
            description=f"Pattern deviation: {pattern_risk:.1f}",
            source="pattern_analysis",
            confidence=0.7
        )
    
    async def train_model(self, historical_data: List[Dict[str, Any]]):
        """Train the anomaly detection model"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            if len(historical_data) < self.min_samples:
                logger.warning(f"Insufficient data for training: {len(historical_data)} < {self.min_samples}")
                return False
            
            # Extract features
            features = []
            for data_point in historical_data:
                feature_vector = []
                for key, value in data_point.items():
                    if isinstance(value, (int, float)):
                        feature_vector.append(value)
                
                if feature_vector:
                    features.append(feature_vector)
            
            if len(features) < self.min_samples:
                logger.warning("Insufficient feature vectors for training")
                return False
            
            # Convert to numpy array
            X = np.array(features)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train isolation forest
            self.isolation_forest.fit(X_scaled)
            
            # Calculate baseline statistics
            self._calculate_baseline_stats(historical_data)
            
            self.is_trained = True
            logger.info(f"Anomaly detection model trained with {len(features)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return False
    
    def _calculate_baseline_stats(self, historical_data: List[Dict[str, Any]]):
        """Calculate baseline statistics for anomaly detection"""
        # Group by region
        regional_data = {}
        
        for data_point in historical_data:
            region = data_point.get("region", "unknown")
            if region not in regional_data:
                regional_data[region] = []
            regional_data[region].append(data_point)
        
        # Calculate statistics for each region
        for region, data_points in regional_data.items():
            if len(data_points) < 3:
                continue
            
            # Extract numeric metrics
            metrics = {}
            for data_point in data_points:
                for key, value in data_point.items():
                    if isinstance(value, (int, float)) and key != "region":
                        if key not in metrics:
                            metrics[key] = []
                        metrics[key].append(value)
            
            # Calculate statistics
            region_stats = {}
            for metric_name, values in metrics.items():
                if len(values) > 1:
                    region_stats[metric_name] = {
                        "mean": np.mean(values),
                        "std": np.std(values),
                        "min": np.min(values),
                        "max": np.max(values),
                        "count": len(values)
                    }
            
            if region_stats:
                self.baseline_stats[region] = region_stats
        
        # Calculate global statistics
        global_metrics = {}
        for data_point in historical_data:
            for key, value in data_point.items():
                if isinstance(value, (int, float)) and key != "region":
                    if key not in global_metrics:
                        global_metrics[key] = []
                    global_metrics[key].append(value)
        
        for metric_name, values in global_metrics.items():
            if len(values) > 1:
                self.baseline_stats[metric_name] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "count": len(values)
                }
    
    def get_anomaly_summary(self, risk_scores: List[RiskScore]) -> Dict[str, Any]:
        """Get summary of anomaly detection results"""
        if not risk_scores:
            return {"summary": "no_data"}
        
        # Count anomalies
        anomalies = [s for s in risk_scores if s.overall_score > 70.0]
        
        # Calculate statistics
        scores = [s.overall_score for s in risk_scores]
        
        return {
            "total_analyses": len(risk_scores),
            "anomalies_detected": len(anomalies),
            "anomaly_rate": len(anomalies) / len(risk_scores) if risk_scores else 0,
            "average_anomaly_score": np.mean(scores),
            "max_anomaly_score": max(scores),
            "min_anomaly_score": min(scores),
            "anomaly_std": np.std(scores),
            "is_model_trained": self.is_trained,
            "baseline_regions": list(self.baseline_stats.keys())
        }
    
    def get_detection_capabilities(self) -> Dict[str, Any]:
        """Get anomaly detection capabilities"""
        return {
            "contamination": self.contamination,
            "window_size": self.window_size,
            "min_samples": self.min_samples,
            "z_score_threshold": self.z_score_threshold,
            "is_trained": self.is_trained,
            "baseline_regions": len(self.baseline_stats),
            "supported_methods": [
                "statistical_anomaly",
                "time_series_anomaly", 
                "isolation_forest",
                "pattern_deviation"
            ]
        }
