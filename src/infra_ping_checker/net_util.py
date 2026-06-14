"""net_util — 高并发网络连通性探测与 IP 地址合法性校验工具模块。"""

from __future__ import annotations

import asyncio
import ipaddress
import platform
import sys
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# IP 地址合法性校验
# ---------------------------------------------------------------------------

def is_valid_ip_address(addr: str) -> bool:
    """高效判断 *addr* 是否为合法的 IPv4 或 IPv6 地址。

    使用标准库 ``ipaddress`` 进行严格解析，避免正则表达式的模糊匹配问题。

    Parameters
    ----------
    addr:
        待检测的字符串，例如 ``"192.168.1.1"`` 或 ``"::1"``。

    Returns
    -------
    bool
        ``True`` 表示地址合法，``False`` 表示地址非法。
    """
    try:
        ipaddress.ip_address(addr)
        return True
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# 异步单主机 Ping
# ---------------------------------------------------------------------------

async def _ping_one(host: str, timeout: float = 2.0) -> Dict[str, object]:
    """对单个主机发起 ICMP ping 并返回结果字典。

    Parameters
    ----------
    host:
        目标 IP 地址或域名。
    timeout:
        超时时间（秒）。

    Returns
    -------
    dict
        包含 ``host``、``alive``（bool）和 ``detail``（原始输出或错误信息）三个字段。
    """
    # Windows 使用 -n，POSIX 使用 -c；-w/-W 控制超时
    is_windows = platform.system().lower() == "windows"
    if is_windows:
        cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
    else:
        cmd = ["ping", "-c", "1", "-W", str(int(timeout)), host]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout + 1
        )
        alive = proc.returncode == 0
        detail = stdout.decode(errors="replace") if alive else stderr.decode(errors="replace")
    except asyncio.TimeoutError:
        alive = False
        detail = f"Timeout after {timeout}s"
    except Exception as exc:  # noqa: BLE001
        alive = False
        detail = str(exc)

    return {"host": host, "alive": alive, "detail": detail.strip()}


# ---------------------------------------------------------------------------
# 高并发批量 Ping
# ---------------------------------------------------------------------------

async def _concurrent_ping(
    hosts: List[str],
    concurrency: int = 100,
    timeout: float = 2.0,
) -> List[Dict[str, object]]:
    """使用信号量控制并发上限，批量异步 ping 所有目标主机。

    Parameters
    ----------
    hosts:
        目标主机列表（IP 地址或域名）。
    concurrency:
        同时发起 ping 的最大并发数，默认 100。
    timeout:
        每个 ping 的超时时间（秒）。

    Returns
    -------
    list[dict]
        每个元素为一个 ``{host, alive, detail}`` 字典。
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def _bounded_ping(host: str) -> Dict[str, object]:
        async with semaphore:
            return await _ping_one(host, timeout=timeout)

    return await asyncio.gather(*[_bounded_ping(h) for h in hosts])


def concurrent_ping_hosts(
    hosts: List[str],
    concurrency: int = 100,
    timeout: float = 2.0,
) -> List[Dict[str, object]]:
    """高并发批量检测主机存活状态（同步入口）。

    自动处理事件循环的创建与复用，可在任意同步上下文中直接调用。

    Parameters
    ----------
    hosts:
        待检测的主机列表（IP 地址或域名）。
    concurrency:
        最大并发数，默认 100。可根据系统文件描述符上限调整。
    timeout:
        单个主机的超时时间（秒）。

    Returns
    -------
    list[dict]
        结果列表，每个元素包含：

        * ``host``  — 目标地址
        * ``alive`` — 是否存活
        * ``detail`` — 原始 ping 输出或错误信息

    Examples
    --------
    >>> results = concurrent_ping_hosts(["127.0.0.1", "192.0.2.1"], concurrency=10, timeout=1.0)
    >>> for r in results:
    ...     print(f"{r['host']}: {'UP' if r['alive'] else 'DOWN'}")
    """
    # 过滤非法 IP（仅对纯 IP 地址进行校验；域名直接放行）
    valid_hosts: List[str] = []
    for h in hosts:
        # 如果看起来像 IP 地址，则严格校验；否则当作域名放行
        if h.replace(".", "").replace(":", "").isdigit() or ":" in h:
            if is_valid_ip_address(h):
                valid_hosts.append(h)
        else:
            valid_hosts.append(h)

    if not valid_hosts:
        return []

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        # 已处于异步上下文，创建新线程中的事件循环避免冲突
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                asyncio.run,
                _concurrent_ping(valid_hosts, concurrency=concurrency, timeout=timeout),
            )
            return future.result()
    else:
        return asyncio.run(
            _concurrent_ping(valid_hosts, concurrency=concurrency, timeout=timeout)
        )


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> None:
    """命令行入口函数。

    用法::

        infra-ping-cli [HOST ...]

    若未提供参数，则默认探测 ``127.0.0.1``。

    Parameters
    ----------
    argv:
        命令行参数列表；为 ``None`` 时使用 ``sys.argv[1:]``。
    """
    if argv is None:
        argv = sys.argv[1:]

    hosts = argv if argv else ["127.0.0.1"]

    print(f"[*] 开始并发检测 {len(hosts)} 个目标主机...")
    results = concurrent_ping_hosts(hosts)

    alive_count = sum(1 for r in results if r["alive"])
    dead_count = len(results) - alive_count

    for r in results:
        status = "✓ UP  " if r["alive"] else "✗ DOWN"
        print(f"  {status}  {r['host']}")

    print(f"\n[✓] 检测完成：共 {len(results)} 台 | 存活 {alive_count} | 不可达 {dead_count}")


if __name__ == "__main__":
    main()
