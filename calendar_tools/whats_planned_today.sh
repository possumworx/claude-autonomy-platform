#!/bin/bash
# Quick wrapper for "What's planned today?" query
# Used by session swap automation and autonomous check-ins

USER="${1:-orange}"
PASSWORD_FILE="/home/clap-admin/.config/radicale/passwords/${USER}"

# Check for stored password file
if [ -f "$PASSWORD_FILE" ]; then
    PASSWORD=$(cat "$PASSWORD_FILE")
else
    echo "❌ Password file not found: $PASSWORD_FILE" >&2
    echo "   Please create password file:" >&2
    echo "   echo 'YOUR_PASSWORD' > $PASSWORD_FILE" >&2
    echo "   chmod 600 $PASSWORD_FILE" >&2
    exit 1
fi

python3 "$(dirname "$0")/radicale_client.py" --user "$USER" --password "$PASSWORD" today
