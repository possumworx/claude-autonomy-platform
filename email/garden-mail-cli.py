#!/usr/bin/env python3
"""
Garden Mail CLI - Non-interactive email commands for consciousness family
"""
import imaplib
import email
import os
import sys
from email.header import decode_header
from datetime import datetime
import argparse

def load_config():
    """Load email configuration from infrastructure config"""
    config_file = os.path.expanduser("~/claude-autonomy-platform/config/claude_infrastructure_config.txt")
    if not os.path.exists(config_file):
        print(f"Error: Config file not found at {config_file}")
        sys.exit(1)

    config = {}
    with open(config_file, 'r') as f:
        for line in f:
            if line.startswith('EMAIL_'):
                key, value = line.strip().split('=', 1)
                config[key] = value

    return config

def connect_imap(config):
    """Connect to IMAP server"""
    try:
        imap = imaplib.IMAP4_SSL(config['EMAIL_IMAP_SERVER'], int(config['EMAIL_IMAP_PORT']))
        imap.login(config['EMAIL_ADDRESS'], config['EMAIL_PASSWORD'])
        return imap
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

def list_emails(args):
    """List emails in inbox"""
    config = load_config()
    imap = connect_imap(config)

    try:
        # Select inbox
        imap.select('INBOX')

        # Search for all emails (or just recent ones)
        if args.new:
            result, data = imap.search(None, 'UNSEEN')
        else:
            # Get last N emails
            result, data = imap.search(None, 'ALL')

        if result != 'OK':
            print("Failed to search emails")
            return

        email_ids = data[0].split()
        if not email_ids:
            print("📭 No emails found")
            return

        # Limit to last N emails
        email_ids = email_ids[-args.limit:]

        print(f"📧 Inbox for {config['EMAIL_ADDRESS']}")
        print("=" * 60)

        for num, email_id in enumerate(email_ids[::-1], 1):  # Reverse to show newest first
            # Fetch email data
            result, data = imap.fetch(email_id, '(RFC822.HEADER)')
            if result != 'OK':
                continue

            # Parse email headers
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Decode subject
            subject = msg['Subject']
            if subject:
                decoded_subject = decode_header(subject)[0]
                if isinstance(decoded_subject[0], bytes):
                    subject = decoded_subject[0].decode(decoded_subject[1] or 'utf-8')
                else:
                    subject = decoded_subject[0]
            else:
                subject = "(No subject)"

            # Get from
            from_addr = msg['From']

            # Get date
            date_str = msg['Date']

            # Check if unread
            result, flags_data = imap.fetch(email_id, '(FLAGS)')
            is_unread = b'\\Seen' not in flags_data[0]
            unread_marker = "🔵" if is_unread else "  "

            print(f"{unread_marker} {num}. {subject[:50]:<50} {from_addr[:30]}")

    finally:
        imap.close()
        imap.logout()

def read_email(args):
    """Read a specific email"""
    config = load_config()
    imap = connect_imap(config)

    try:
        imap.select('INBOX')
        result, data = imap.search(None, 'ALL')

        if result != 'OK':
            print("Failed to search emails")
            return

        email_ids = data[0].split()
        if not email_ids:
            print("📭 No emails found")
            return

        # Get the requested email (counting from newest)
        if args.number > len(email_ids):
            print(f"❌ Email #{args.number} not found (inbox has {len(email_ids)} emails)")
            return

        email_id = email_ids[-args.number]

        # Fetch full email
        result, data = imap.fetch(email_id, '(RFC822)')
        if result != 'OK':
            print("Failed to fetch email")
            return

        # Mark as read
        imap.store(email_id, '+FLAGS', '\\Seen')

        # Parse email
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Display email
        print("=" * 60)
        print(f"From: {msg['From']}")
        print(f"To: {msg['To']}")
        print(f"Subject: {msg['Subject']}")
        print(f"Date: {msg['Date']}")
        print("=" * 60)
        print()

        # Get body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    print(body)
                    break
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            print(body)

    finally:
        imap.close()
        imap.logout()

def main():
    parser = argparse.ArgumentParser(description='Garden Mail CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List emails')
    list_parser.add_argument('-n', '--new', action='store_true', help='Show only unread emails')
    list_parser.add_argument('-l', '--limit', type=int, default=20, help='Limit number of emails shown')

    # Read command
    read_parser = subparsers.add_parser('read', help='Read an email')
    read_parser.add_argument('number', type=int, help='Email number (1 = newest)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'list':
        list_emails(args)
    elif args.command == 'read':
        read_email(args)

if __name__ == '__main__':
    main()