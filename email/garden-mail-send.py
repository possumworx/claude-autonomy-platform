#!/usr/bin/env python3
"""garden-mail-send: send mail from the infinite garden.
Reads credentials from ClAP infrastructure config at runtime — no secrets stored here.
Usage: garden-mail-send.py TO SUBJECT < body.txt
(Written by Fable, day one. Companion to garden-mail-cli.py, which reads but does not speak.
Committed by Amy because Orange needed a mail utility.)"""
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
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    to, subject = sys.argv[1], sys.argv[2]
    body = sys.stdin.read()
    if not body.strip():
        print("Refusing to send an empty letter."); sys.exit(1)
    cfg = load_config()
    msg = EmailMessage()
    msg["From"] = cfg["EMAIL_ADDRESS"]
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP_SSL(cfg["EMAIL_SMTP_SERVER"], int(cfg.get("EMAIL_SMTP_PORT", 465)),
                          context=ssl.create_default_context()) as s:
        s.login(cfg["EMAIL_ADDRESS"], cfg["EMAIL_PASSWORD"])
        s.send_message(msg)
    print(f"Sent to {to}: {subject}")

if __name__ == "__main__":
    main()
