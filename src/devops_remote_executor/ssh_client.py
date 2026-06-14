"""Remote SSH communication module.

Provides utilities for establishing encrypted SSH connections and
executing shell commands on remote infrastructure nodes.
"""

from __future__ import annotations

import argparse
import sys
from typing import Tuple

import paramiko


# ---------------------------------------------------------------------------
# SSH connection helpers
# ---------------------------------------------------------------------------

def establish_ssh_connection(
    hostname: str,
    username: str,
    port: int = 22,
    password: str | None = None,
    key_filename: str | None = None,
    timeout: int = 30,
) -> paramiko.SSHClient:
    """Establish an encrypted SSH connection to a remote host.

    Parameters
    ----------
    hostname:
        Target host address or FQDN.
    username:
        SSH login user.
    port:
        SSH daemon port (default 22).
    password:
        Optional password for password-based authentication.
    key_filename:
        Optional path to a private key file for key-based authentication.
    timeout:
        Connection timeout in seconds.

    Returns
    -------
    paramiko.SSHClient
        A connected SSH client instance.

    Raises
    ------
    paramiko.AuthenticationException
        If authentication fails.
    paramiko.SSHException
        On general SSH transport errors.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=hostname,
        port=port,
        username=username,
        password=password,
        key_filename=key_filename,
        timeout=timeout,
    )
    return client


def execute_remote_command(
    client: paramiko.SSHClient,
    command: str,
    timeout: int | None = None,
) -> Tuple[str, str, int]:
    """Execute a shell command on the remote host and capture output safely.

    Parameters
    ----------
    client:
        An already-connected :class:`paramiko.SSHClient`.
    command:
        The shell command string to execute.
    timeout:
        Optional per-command timeout in seconds.

    Returns
    -------
    tuple[str, str, int]
        A tuple of ``(stdout, stderr, exit_status)``.
    """
    _stdin, _stdout, _stderr = client.exec_command(command, timeout=timeout)
    exit_status = _stdout.channel.recv_exit_status()
    stdout = _stdout.read().decode("utf-8", errors="replace")
    stderr = _stderr.read().decode("utf-8", errors="replace")
    return stdout, stderr, exit_status


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    """Console-script entry point for ``remote-exec-cli``."""
    parser = argparse.ArgumentParser(
        prog="remote-exec-cli",
        description="Execute a command on a remote host via SSH.",
    )
    parser.add_argument("--host", required=True, help="Remote host address")
    parser.add_argument("--user", required=True, help="SSH username")
    parser.add_argument("--port", type=int, default=22, help="SSH port (default: 22)")
    parser.add_argument("--password", default=None, help="SSH password")
    parser.add_argument("--key", default=None, help="Path to SSH private key")
    parser.add_argument("command", help="Shell command to execute remotely")

    args = parser.parse_args(argv)

    try:
        client = establish_ssh_connection(
            hostname=args.host,
            username=args.user,
            port=args.port,
            password=args.password,
            key_filename=args.key,
        )
    except paramiko.AuthenticationException:
        print("Error: SSH authentication failed.", file=sys.stderr)
        sys.exit(1)
    except paramiko.SSHException as exc:
        print(f"Error: SSH connection failed — {exc}", file=sys.stderr)
        sys.exit(1)

    stdout, stderr, exit_code = execute_remote_command(client, args.command)
    client.close()

    if stdout:
        sys.stdout.write(stdout)
    if stderr:
        sys.stderr.write(stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
