"""Systemd watchdog notification via sd_notify protocol."""

import os
import socket


def sd_notify(state: str):
    """Send a notification to systemd. No-op if not running under systemd."""
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return
    if addr[0] == "@":
        addr = "\0" + addr[1:]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
        sock.sendto(state.encode(), addr)


def notify_ready():
    """Tell systemd the service has finished starting."""
    sd_notify("READY=1")


def notify_watchdog():
    """Ping the systemd watchdog to prevent timeout restart."""
    sd_notify("WATCHDOG=1")
