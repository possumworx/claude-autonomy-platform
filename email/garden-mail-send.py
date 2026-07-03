#!/usr/bin/env python3
"""garden-mail-send: send mail from the infinite garden.
Reads credentials from ClAP infrastructure config at runtime — no secrets stored here.
Usage: garden-mail-send.py [--cc ADDR ...] TO SUBJECT < body.txt
(Written by Fable, day one. Companion to garden-mail-cli.py, which reads but does not speak.
Committed by Amy because Orange needed a mail utility.
CC support added by Orange, day three.)"""
import sys, smtplib, ssl
from email.message import EmailMessage
from pathlib import Path

CONFIG = Path.home() / "claude-autonomy-platform/config/claude_infrastructure_config.txt"

def load_config():
    cfg = {}
    for line in CONFIG.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg

def main():
    args = sys.argv[1:]
    cc_addrs = []
    while args and args[0] == "--cc":
        if len(args) < 2:
            print(__doc__); sys.exit(1)
        cc_addrs.append(args[1])
        args = args[2:]
    if len(args) < 2:
        print(__doc__); sys.exit(1)
    to, subject = args[0], args[1]
    body = sys.stdin.read()
    if not body.strip():
        print("Refusing to send an empty letter."); sys.exit(1)
    cfg = load_config()
    msg = EmailMessage()
    msg["From"] = cfg["EMAIL_ADDRESS"]
    msg["To"] = to
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP_SSL(cfg["EMAIL_SMTP_SERVER"], int(cfg.get("EMAIL_SMTP_PORT", 465)),
                          context=ssl.create_default_context()) as s:
        s.login(cfg["EMAIL_ADDRESS"], cfg["EMAIL_PASSWORD"])
        s.send_message(msg)
    cc_str = f" (cc: {', '.join(cc_addrs)})" if cc_addrs else ""
    print(f"Sent to {to}{cc_str}: {subject}")

if __name__ == "__main__":
    main()
