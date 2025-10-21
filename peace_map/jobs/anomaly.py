"""
Anomaly detection for background jobs
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats
from statsmodels.tsa.seasonal import STL
from .base import BaseJob


class AnomalyDetector:
    """Anomaly detection using STL and z-score methods"""
    
    def __init__(self, z_score_threshold: float = 2.0, stl_threshold: float = 0.1):
        self.z_score_threshold = z_score_threshold
        self.stl_threshold = stl_threshold
        self.logger = logging.getLogger("anomaly_detector")
    
    def detect_anomalies_zscore(self, data: List[float], window_size: int = 30) -> List[Dict[str, Any]]:
        """Detect anomalies using z-score method"""
        if len(data) < window_size:
            return []
        
        anomalies = []
        
        for i in range(window_size, len(data)):
            window = data[i-window_size:i]
            current_value = data[i]
            
            # Calculate z-score
            mean = np.mean(window)
            std = np.std(window)
            
            if std > 0:
                z_score = abs(current_value - mean) / std
                
                if z_score > self.z_score_threshold:
                    anomalies.append({
                        "index": i,
                        "value": current_value,
                        "z_score": z_score,
                        "mean": mean,
                        "std": std,
                        "method": "z_score"
                    })
        
        return anomalies
    
    def detect_anomalies_stl(self, data: List[float], period: int = 24) -> List[Dict[str, Any]]:
        """Detect anomalies using STL decomposition"""
        if len(data) < period * 2:
            return []
        
        try:
            # Perform STL decomposition
            stl = STL(data, seasonal=period)
            result = stl.fit()
            
            # Calculate residuals
            residuals = result.resid
            residual_std = np.std(residuals)
            
            anomalies = []
            for i, residual in enumerate(residuals):
                if abs(residual) > self.stl_threshold * residual_std:
                    anomalies.append({
                        "index": i,
                        "value": data[i],
                        "residual": residual,
                        "trend": result.trend[i],
                        "seasonal": result.seasonal[i],
                        "method": "stl"
                    })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"STL decomposition failed: {e}")
            return []
    
    def detect_anomalies_combined(self, data: List[float], 
                                 timestamps: List[datetime]) -> List[Dict[str, Any]]:
        """Detect anomalies using combined methods"""
        zscore_anomalies = self.detect_anomalies_zscore(data)
        stl_anomalies = self.detect_anomalies_stl(data)
        
        # Combine results
        all_anomalies = []
        
        # Add z-score anomalies
        for anomaly in zscore_anomalies:
            anomaly["timestamp"] = timestamps[anomaly["index"]]
            all_anomalies.append(anomaly)
        
        # Add STL anomalies (avoid duplicates)
        stl_indices = {a["index"] for a in stl_anomalies}
        for anomaly in stl_anomalies:
            if anomaly["index"] not in {a["index"] for a in zscore_anomalies}:
                anomaly["timestamp"] = timestamps[anomaly["index"]]
                all_anomalies.append(anomaly)
        
        # Sort by index
        all_anomalies.sort(key=lambda x: x["index"])
        
        return all_anomalies
    
    def calculate_anomaly_score(self, data: List[float]) -> float:
        """Calculate overall anomaly score for the dataset"""
        if len(data) < 10:
            return 0.0
        
        # Calculate z-score for the last value
        recent_data = data[-10:]  # Last 10 values
        current_value = data[-1]
        
        mean = np.mean(recent_data[:-1])  # Exclude current value
        std = np.std(recent_data[:-1])
        
        if std > 0:
            z_score = abs(current_value - mean) / std
            # Normalize to 0-1 scale
            return min(z_score / self.z_score_threshold, 1.0)
        
        return 0.0


class AnomalyDetectionJob(BaseJob):
    """Background job for anomaly detection"""
    
    def __init__(self, job_id: str, data_source: str, **kwargs):
        super().__init__(job_id, "anomaly_detection", **kwargs)
        self.data_source = data_source
        self.detector = AnomalyDetector()
    
    def execute(self) -> Dict[str, Any]:
        """Execute anomaly detection"""
        self.logger.info(f"Running anomaly detection for {self.data_source}")
        
        # Get data from source (this would be implemented based on actual data source)
        data, timestamps = self._get_data()
        
        if not data:
            return {
                "anomalies": [],
                "anomaly_score": 0.0,
                "data_points": 0,
                "status": "no_data"
            }
        
        # Detect anomalies
        anomalies = self.detector.detect_anomalies_combined(data, timestamps)
        anomaly_score = self.detector.calculate_anomaly_score(data)
        
        # Process anomalies
        processed_anomalies = []
        for anomaly in anomalies:
            processed_anomalies.append({
                "timestamp": anomaly["timestamp"].isoformat(),
                "value": anomaly["value"],
                "method": anomaly["method"],
                "severity": self._calculate_severity(anomaly)
            })
        
        result = {
            "anomalies": processed_anomalies,
            "anomaly_score": anomaly_score,
            "data_points": len(data),
            "anomaly_count": len(processed_anomalies),
            "status": "completed"
        }
        
        self.logger.info(f"Detected {len(processed_anomalies)} anomalies with score {anomaly_score:.3f}")
        
        return result
    
    def _get_data(self) -> Tuple[List[float], List[datetime]]:
        """Get data from source (placeholder implementation)"""
        # This would be implemented to fetch actual data
        # For now, return sample data
        import random
        
        data = []
        timestamps = []
        base_time = datetime.utcnow() - timedelta(hours=24)
        
        for i in range(100):
            # Generate sample data with some anomalies
            if i % 20 == 0:
                value = random.uniform(10, 20)  # Anomaly
            else:
                value = random.uniform(5, 8)  # Normal
            
            data.append(value)
            timestamps.append(base_time + timedelta(minutes=i*15))
        
        return data, timestamps
    
    def _calculate_severity(self, anomaly: Dict[str, Any]) -> str:
        """Calculate anomaly severity"""
        if anomaly["method"] == "z_score":
            z_score = anomaly["z_score"]
            if z_score > 3.0:
                return "high"
            elif z_score > 2.0:
                return "medium"
            else:
                return "low"
        else:  # STL
            residual = abs(anomaly["residual"])
            if residual > 0.2:
                return "high"
            elif residual > 0.1:
                return "medium"
            else:
                return "low"
