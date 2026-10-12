"""
Main entry point for AI-Driven Cloud Cost Optimization & Anomaly Detection.
Runs telemetry analysis, statistical anomaly detection, rightsizing, and forecasting.
"""
import os
import yaml
from tabulate import tabulate

from src.cost_analyzer import CostAnalyzer
from src.anomaly_detector import AnomalyDetector
from src.rightsizer import ResourceRightsizer
from src.capacity_forecaster import CapacityForecaster


def load_config():
    config_path = os.path.join("config", "thresholds.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main():
    print("=" * 75)
    print("  AI-DRIVEN CLOUD COST OPTIMIZATION & ANOMALY DETECTION ENGINE")
    print("=" * 75)

    config = load_config()
    anom_cfg = config.get("anomaly_detection", {})

    # 1. Telemetry Ingestion & Summary
    print("\n[+] 1. INGESTING CLOUD BILLING TELEMETRY...")
    spend_data_path = os.path.join("sample_data", "aws_daily_spend.json")
    analyzer = CostAnalyzer(spend_data_path)
    df_pivot = analyzer.get_service_daily_totals()
    summary_stats = analyzer.get_summary_statistics()

    summary_rows = []
    for service, stats in summary_stats.items():
        summary_rows.append([service, f"${stats['total_spend']:,.2f}", f"${stats['avg_daily_spend']:,.2f}", f"${stats['max_daily_spend']:,.2f}"])

    print(tabulate(summary_rows, headers=["Service", "Total Spend", "Avg Daily Spend", "Max Daily Spend"], tablefmt="grid"))

    # 2. Anomaly Detection
    print("\n[+] 2. RUNNING STATISTICAL ANOMALY DETECTION...")
    detector = AnomalyDetector(
        rolling_window=anom_cfg.get("rolling_window_days", 7),
        spike_threshold_pct=anom_cfg.get("cost_spike_threshold_percent", 25.0),
        z_score_threshold=anom_cfg.get("z_score_threshold", 2.0)
    )

    anomalies = detector.detect_zscore_anomalies(df_pivot)
    if anomalies:
        anomaly_rows = []
        for anom in anomalies:
            anomaly_rows.append([anom["date"], anom["service"], f"${anom['cost']:.2f}", f"${anom['baseline_cost']:.2f}", f"+{anom['spike_percent']}%", anom["severity"]])
        print(tabulate(anomaly_rows, headers=["Date", "Service", "Cost", "7-Day Baseline", "Spike %", "Severity"], tablefmt="grid"))
    else:
        print("  [✓] No abnormal cost spikes detected.")

    # 3. Infrastructure Rightsizing Audit
    print("\n[+] 3. AUDITING RESOURCES FOR IDLE ASSETS & RIGHTSIZING...")
    inv_path = os.path.join("sample_data", "resource_inventory.json")
    rightsizer = ResourceRightsizer(inv_path)
    audit_results = rightsizer.audit_resources()

    rec_rows = []
    for rec in audit_results["recommendations"]:
        rec_rows.append([rec["resource_id"], rec["type"], rec["issue"], rec["action"], f"${rec['monthly_savings_usd']:.2f}/mo", rec["owner"]])

    print(tabulate(rec_rows, headers=["Resource ID", "Type", "Observed Issue", "Recommended Action", "Monthly Savings", "Owner"], tablefmt="grid"))
    print(f"\n  [★] TOTAL PROJECTED MONTHLY SAVINGS: ${audit_results['total_monthly_savings_usd']:,.2f}")
    print(f"  [★] TOTAL PROJECTED ANNUAL SAVINGS:  ${audit_results['annual_projected_savings_usd']:,.2f}")

    # 4. Proactive Capacity Forecasting
    print("\n[+] 4. GENERATING PROACTIVE AUTO-SCALING FORECAST...")
    traffic_csv_path = os.path.join("sample_data", "cloudwatch_traffic.csv")
    forecaster = CapacityForecaster(traffic_csv_path)
    forecast_actions = forecaster.forecast_proactive_scaling()

    forecast_rows = []
    for act in forecast_actions:
        forecast_rows.append([act["hour_of_day"], act["historical_peak_cpu"], act["recommended_action"]])

    print(tabulate(forecast_rows, headers=["Hour (UTC)", "Peak CPU", "Proactive Scaling Action"], tablefmt="grid"))

    print("\n" + "=" * 75)
    print("  OPTIMIZATION AUDIT COMPLETE — REPORT READY FOR DISPATCH")
    print("=" * 75)


if __name__ == "__main__":
    main()