"""Remote communication module for establishing encrypted SSH connections
and executing shell commands on remote hosts."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

import paramiko


@dataclass
class CommandResult:
    """Encapsulates the result of a remote command execution."""

    exit_code: int
    stdout: str
    stderr: str


def establish_ssh_connection(
    hostname: str,
    port: int = 22,
    username: Optional[str] = None,
    password: Optional[str] = None,
    key_filename: Optional[str] = None,
    timeout: float = 10.0,
) -> paramiko.SSHClient:
    """Establish an encrypted SSH connection to a remote host.

    Args:
        hostname: Target host address.
        port: SSH port number.
        username: Login username.
        password: Login password (mutually exclusive with *key_filename* in
            most scenarios, but both may be supplied for key passphrase).
        key_filename: Path to a private key file for public-key authentication.
        timeout: Connection timeout in seconds.

    Returns:
        A connected ``paramiko.SSHClient`` instance ready for command execution.

    Raises:
        paramiko.AuthenticationException: If authentication fails.
        paramiko.SSHException: On general SSH protocol errors.
        socket.timeout: When the connection attempt times out.
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
    timeout: Optional[float] = None,
) -> CommandResult:
    """Execute a shell command on the remote host and capture output safely.

    Args:
        client: An active ``paramiko.SSHClient`` connection.
        command: The shell command string to execute.
        timeout: Optional per-command timeout in seconds.

    Returns:
        A ``CommandResult`` containing exit code, stdout, and stderr.
    """
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    stdin.close()

    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    exit_code = stdout.channel.recv_exit_status()

    return CommandResult(exit_code=exit_code, stdout=out, stderr=err)


def main() -> None:
    """CLI entry point for remote-exec-cli."""
    parser = argparse.ArgumentParser(
        prog="remote-exec-cli",
        description="Execute commands on remote hosts over SSH.",
    )
    parser.add_argument("hostname", help="Target host address")
    parser.add_argument("command", help="Shell command to execute remotely")
    parser.add_argument("-p", "--port", type=int, default=22, help="SSH port")
    parser.add_argument("-u", "--user", default=None, help="SSH username")
    parser.add_argument("-k", "--key", default=None, help="Path to private key file")
    parser.add_argument(
        "-t", "--timeout", type=float, default=10.0, help="Connection timeout"
    )

    args = parser.parse_args()

    try:
        client = establish_ssh_connection(
            hostname=args.hostname,
            port=args.port,
            username=args.user,
            key_filename=args.key,
            timeout=args.timeout,
        )
    except Exception as exc:
        print(f"Connection failed: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        result = execute_remote_command(client, args.command)
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        sys.exit(result.exit_code)
    finally:
        client.close()


if __name__ == "__main__":
    main()
