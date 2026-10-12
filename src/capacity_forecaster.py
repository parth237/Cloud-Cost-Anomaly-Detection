"""
Predictive Capacity & Auto-Scaling Forecaster.
Analyzes historical CloudWatch metrics to forecast upcoming peak traffic.
"""
import logging
from typing import Dict, List
import pandas as pd

logger = logging.getLogger(__name__)


class CapacityForecaster:
    def __init__(self, metrics_csv_path: str):
        self.metrics_path = metrics_csv_path
        self.df = pd.DataFrame()

    def load_metrics(self) -> pd.DataFrame:
        """Load historical CloudWatch metric telemetry from CSV."""
        self.df = pd.read_csv(self.metrics_path)
        self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])
        return self.df

    def forecast_proactive_scaling(self) -> List[Dict]:
        """
        Identifies recurring peak hours and recommends proactive pre-scaling
        30 minutes before traffic surges.
        """
        if self.df.empty:
            self.load_metrics()

        # Group metrics by hour of day to detect recurring traffic patterns
        self.df["hour"] = self.df["timestamp"].dt.hour
        hourly_stats = self.df.groupby("hour")["cpu_utilization"].agg(["mean", "max"]).reset_index()

        scaling_actions = []
        for _, row in hourly_stats.iterrows():
            hour = int(row["hour"])
            max_cpu = round(float(row["max"]), 1)

            # If historical peak CPU crosses 80%, recommend pre-scaling
            if max_cpu > 80.0:
                scaling_actions.append({
                    "hour_of_day": f"{hour:02d}:00 UTC",
                    "historical_peak_cpu": f"{max_cpu}%",
                    "recommended_action": "Proactively pre-scale ASG +2 instances 30m prior",
                    "reason": "Predicted traffic surge based on historical seasonal pattern"
                })

        return scaling_actions