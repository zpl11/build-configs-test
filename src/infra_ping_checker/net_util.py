"""Network probing utilities for high-concurrency host liveness detection."""

from __future__ import annotations

import asyncio
import ipaddress
import platform
import subprocess
import sys
from typing import Dict, List


def is_valid_ip_address(addr: str) -> bool:
    """Return *True* if *addr* is a syntactically valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(addr)
        return True
    except ValueError:
        return False


async def _ping_one(host: str, timeout: int = 2) -> Dict[str, object]:
    """Ping a single host and return a result dict."""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_flag = "-w" if platform.system().lower() == "windows" else "-W"
    cmd = ["ping", param, "1", timeout_flag, str(timeout * 1000 if platform.system().lower() == "windows" else timeout), host]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=timeout + 2)
        alive = proc.returncode == 0
    except (asyncio.TimeoutError, OSError):
        alive = False

    return {"host": host, "alive": alive}


async def _ping_all(hosts: List[str], concurrency: int = 64, timeout: int = 2) -> List[Dict[str, object]]:
    """Run ping checks on *hosts* with bounded concurrency."""
    sem = asyncio.Semaphore(concurrency)

    async def _guarded(h: str) -> Dict[str, object]:
        async with sem:
            return await _ping_one(h, timeout=timeout)

    return list(await asyncio.gather(*(_guarded(h) for h in hosts)))


def concurrent_ping_hosts(
    hosts: List[str],
    concurrency: int = 64,
    timeout: int = 2,
) -> List[Dict[str, object]]:
    """Check reachability of *hosts* using high-concurrency async ping.

    Parameters
    ----------
    hosts:
        List of IP addresses or hostnames to probe.
    concurrency:
        Maximum number of simultaneous ping subprocesses.
    timeout:
        Per-host timeout in seconds.

    Returns
    -------
    list[dict]:
        Each dict contains ``{"host": str, "alive": bool}``.
    """
    return asyncio.run(_ping_all(hosts, concurrency=concurrency, timeout=timeout))


def main() -> None:
    """CLI entry point: accept hosts as arguments and report liveness."""
    hosts = sys.argv[1:]
    if not hosts:
        print("Usage: infra-ping-cli <host1> [host2] ...")
        raise SystemExit(1)

    results = concurrent_ping_hosts(hosts)
    for r in results:
        status = "ALIVE" if r["alive"] else "UNREACHABLE"
        print(f"  {r['host']:>39s}  [{status}]")
