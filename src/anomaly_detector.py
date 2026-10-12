"""
Statistical and ML Anomaly Detection Engine.
Identifies cost spikes using rolling baselines and Isolation Forest.
"""
import logging
from typing import List, Dict
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class AnomalyDetector:
    def __init__(self, rolling_window: int = 7, spike_threshold_pct: float = 25.0, z_score_threshold: float = 2.0):
        self.rolling_window = rolling_window
        self.spike_threshold_pct = spike_threshold_pct
        self.z_score_threshold = z_score_threshold

    def detect_zscore_anomalies(self, df_pivot: pd.DataFrame) -> List[Dict]:
        """
        Detect cost anomalies by comparing daily spend to rolling 7-day average.
        """
        anomalies = []
        for service in df_pivot.columns:
            series = df_pivot[service]
            # Calculate rolling 7-day average and standard deviation
            rolling_mean = series.rolling(window=self.rolling_window, min_periods=3).mean()
            rolling_std = series.rolling(window=self.rolling_window, min_periods=3).std().replace(0, 0.01)

            z_scores = (series - rolling_mean) / rolling_std

            for date, cost in series.items():
                z = z_scores.get(date, 0)
                mean = rolling_mean.get(date, cost)
                pct_spike = ((cost - mean) / mean) * 100 if mean > 0 else 0

                # Flag if cost spiked above our threshold
                if z >= self.z_score_threshold and pct_spike >= self.spike_threshold_pct:
                    anomalies.append({
                        "date": str(date.strftime("%Y-%m-%d")),
                        "service": service,
                        "cost": round(float(cost), 2),
                        "baseline_cost": round(float(mean), 2),
                        "spike_percent": round(float(pct_spike), 1),
                        "z_score": round(float(z), 2),
                        "severity": "CRITICAL" if pct_spike > 100 else "WARNING"
                    })
        return anomalies

    def detect_isolation_forest(self, df_pivot: pd.DataFrame) -> List[Dict]:
        """
        Detect outliers using scikit-learn Isolation Forest.
        """
        ml_anomalies = []
        for service in df_pivot.columns:
            data = df_pivot[[service]].values
            if len(data) < 5:
                continue
            iso = IsolationForest(contamination=0.08, random_state=42)
            preds = iso.fit_predict(data)

            for i, pred in enumerate(preds):
                if pred == -1:  # -1 represents an outlier
                    date = df_pivot.index[i]
                    ml_anomalies.append({
                        "date": str(date.strftime("%Y-%m-%d")),
                        "service": service,
                        "cost": round(float(data[i][0]), 2),
                        "method": "IsolationForest"
                    })
        return ml_anomalies