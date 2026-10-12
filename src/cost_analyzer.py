"""
Cloud Cost Telemetry Ingestion and Analyzer.
Reads billing telemetry and aggregates daily spend by service.
"""
import json
import logging
from typing import Dict, List
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class CostAnalyzer:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.df = pd.DataFrame()

    def load_telemetry(self) -> pd.DataFrame:
        """Load and parse billing telemetry JSON data."""
        try:
            with open(self.data_path, "r") as f:
                raw_data = json.load(f)
            self.df = pd.DataFrame(raw_data)
            self.df["date"] = pd.to_datetime(self.df["date"])
            self.df["cost"] = pd.to_numeric(self.df["cost"])
            logger.info(f"Loaded {len(self.df)} billing records from {self.data_path}")
            return self.df
        except Exception as e:
            logger.error(f"Failed to load telemetry data: {e}")
            raise

    def get_service_daily_totals(self) -> pd.DataFrame:
        """Pivot telemetry to show daily cost per cloud service."""
        if self.df.empty:
            self.load_telemetry()
        pivot = self.df.pivot_table(index="date", columns="service", values="cost", aggfunc="sum").fillna(0)
        return pivot

    def get_summary_statistics(self) -> Dict[str, Dict[str, float]]:
        """Calculate mean, min, max daily spend for each service."""
        if self.df.empty:
            self.load_telemetry()
        summary = {}
        for service, group in self.df.groupby("service"):
            summary[service] = {
                "total_spend": round(group["cost"].sum(), 2),
                "avg_daily_spend": round(group["cost"].mean(), 2),
                "max_daily_spend": round(group["cost"].max(), 2),
            }
        return summary