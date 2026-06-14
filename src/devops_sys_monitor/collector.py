"""System metrics collector module for server monitoring."""

import json
import platform
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import psutil


def get_system_metrics() -> Dict[str, Any]:
    """Collect and return core system metrics.

    Returns a dictionary containing:
      - hostname:          system hostname
      - platform:          OS platform string
      - timestamp:         ISO-8601 collection time
      - cpu:               CPU usage percentage and core count
      - memory:            virtual memory statistics
      - swap:              swap memory statistics
      - disk:              root partition disk usage
      - network:           aggregated network I/O counters
    """
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    net = psutil.net_io_counters()

    # Collect disk usage for all mounted partitions
    disk_partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disk_partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent": usage.percent,
            })
        except PermissionError:
            continue

    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "timestamp": datetime.now().isoformat(),
        "cpu": {
            "count": psutil.cpu_count(logical=True),
            "percent_overall": sum(cpu_percent) / len(cpu_percent) if cpu_percent else 0.0,
            "percent_per_cpu": cpu_percent,
        },
        "memory": {
            "total_bytes": mem.total,
            "available_bytes": mem.available,
            "used_bytes": mem.used,
            "percent": mem.percent,
        },
        "swap": {
            "total_bytes": swap.total,
            "used_bytes": swap.used,
            "free_bytes": swap.free,
            "percent": swap.percent,
        },
        "disk": disk_partitions,
        "network": {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        },
    }


def check_disk_alert(
    threshold_percent: float = 85.0,
    mountpoint: Optional[str] = None,
) -> Dict[str, Any]:
    """Check whether any disk partition exceeds the usage threshold.

    Args:
        threshold_percent: Usage percentage that triggers an alert (0-100).
        mountpoint:        If given, only check this specific mountpoint.
                           When *None*, all mounted partitions are checked.

    Returns a dictionary with:
      - alert:   bool  - True when at least one partition is over threshold
      - details: list  - per-partition status entries
    """
    alerts: list = []
    partitions = psutil.disk_partitions(all=False)

    for part in partitions:
        if mountpoint and part.mountpoint != mountpoint:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue

        entry = {
            "device": part.device,
            "mountpoint": part.mountpoint,
            "percent": usage.percent,
            "threshold_percent": threshold_percent,
            "triggered": usage.percent >= threshold_percent,
        }
        alerts.append(entry)

    return {
        "alert": any(e["triggered"] for e in alerts),
        "details": alerts,
    }


def _format_bytes(n: int) -> str:
    """Human-readable byte size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def main() -> None:
    """CLI entry point: collect metrics, check disk alerts, and print JSON."""
    metrics = get_system_metrics()
    disk_alert = check_disk_alert()

    output = {
        "metrics": metrics,
        "disk_alert": disk_alert,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))

    if disk_alert["alert"]:
        triggered = [d["mountpoint"] for d in disk_alert["details"] if d["triggered"]]
        print(
            f"\n[ALERT] Disk usage exceeds threshold on: {', '.join(triggered)}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
