"""
Cloud Resource Rightsizing & Cost Optimization Engine.
Audits underutilized EC2 instances, unattached EBS volumes, and idle RDS replicas.
"""
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ResourceRightsizer:
    def __init__(self, inventory_path: str):
        self.inventory_path = inventory_path
        self.inventory = []

    def load_inventory(self) -> List[Dict]:
        """Load cloud resource inventory from JSON."""
        with open(self.inventory_path, "r") as f:
            self.inventory = json.load(f)
        return self.inventory

    def audit_resources(self) -> Dict:
        """
        Audits resources against utilization baselines and returns dollar savings.
        """
        if not self.inventory:
            self.load_inventory()

        recommendations = []
        total_monthly_savings = 0.0

        for item in self.inventory:
            res_type = item.get("resource_type")

            # 1. Underutilized EC2 instances (CPU < 10%)
            if res_type == "ec2_instance":
                avg_cpu = item.get("avg_cpu_percent", 0)
                current_cost = item.get("current_monthly_cost", 0)
                if avg_cpu < 10.0:
                    potential_saving = round(current_cost * 0.65, 2)
                    total_monthly_savings += potential_saving
                    recommendations.append({
                        "resource_id": item["resource_id"],
                        "type": "EC2 Instance",
                        "issue": f"Low CPU usage ({avg_cpu}% avg)",
                        "action": "Downsize instance to t3.large",
                        "monthly_savings_usd": potential_saving,
                        "owner": item.get("owner")
                    })

            # 2. Unattached EBS volumes (Zombie assets > 14 days)
            elif res_type == "ebs_volume":
                if item.get("state") == "available" and item.get("days_unattached", 0) > 14:
                    cost = item.get("current_monthly_cost", 0)
                    total_monthly_savings += cost
                    recommendations.append({
                        "resource_id": item["resource_id"],
                        "type": "EBS Volume",
                        "issue": f"Unattached for {item.get('days_unattached')} days",
                        "action": "Create snapshot & delete orphaned disk",
                        "monthly_savings_usd": cost,
                        "owner": item.get("owner")
                    })

            # 3. Idle RDS database replicas (0 active connections)
            elif res_type == "rds_instance":
                avg_conn = item.get("avg_connections", 0)
                cost = item.get("current_monthly_cost", 0)
                if avg_conn == 0:
                    total_monthly_savings += cost
                    recommendations.append({
                        "resource_id": item["resource_id"],
                        "type": "RDS Instance",
                        "issue": "0 active connections",
                        "action": "Decommission unused read replica",
                        "monthly_savings_usd": cost,
                        "owner": item.get("owner")
                    })

        return {
            "total_monthly_savings_usd": round(total_monthly_savings, 2),
            "annual_projected_savings_usd": round(total_monthly_savings * 12, 2),
            "recommendations": recommendations
        }