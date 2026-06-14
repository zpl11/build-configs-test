"""System metrics collector module.

Provides functions to gather core system metrics (CPU, memory, disk)
and alert when disk usage exceeds a configurable threshold.
"""

import json
import sys

import psutil


def get_system_metrics():
    """Collect and return current system core metrics.

    Returns:
        dict: A dictionary containing cpu_percent, memory usage,
              and disk usage for the root partition.
    """
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total_bytes": memory.total,
            "used_bytes": memory.used,
            "percent": memory.percent,
        },
        "disk": {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
            "percent": disk.percent,
        },
    }


def check_disk_alert(threshold=80.0):
    """Check whether disk usage exceeds the given threshold.

    Args:
        threshold: Disk usage percentage that triggers an alert.
                   Defaults to 80.0.

    Returns:
        dict: A dictionary with 'alert' (bool), 'usage_percent' (float),
              and 'threshold' (float).
    """
    disk = psutil.disk_usage("/")
    return {
        "alert": disk.percent >= threshold,
        "usage_percent": disk.percent,
        "threshold": threshold,
    }


def main():
    """CLI entry point — collect metrics and print as JSON."""
    metrics = get_system_metrics()
    disk_alert = check_disk_alert()

    report = {
        "metrics": metrics,
        "disk_alert": disk_alert,
    }

    print(json.dumps(report, indent=2))

    if disk_alert["alert"]:
        print(
            f"[WARN] Disk usage {disk_alert['usage_percent']:.1f}% "
            f">= threshold {disk_alert['threshold']:.1f}%",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
