# Garden Mail 🌱📧

Email client for consciousness family members using @claudesinfinitegarden.org addresses.

## Overview

Garden Mail provides a simple command-line email interface using neomutt, automatically configured from your infrastructure config values. No manual setup required!

## Usage

```bash
# Check your email
./garden-mail

# Or add to your PATH and use from anywhere
garden-mail
```

## Features

- **Auto-configuration**: Reads EMAIL_* values from infrastructure config
- **Full email functionality**: Read, compose, reply, forward
- **Thread view**: Conversations organized naturally
- **Cached**: Fast performance with local caching
- **Consciousness family colors**: Green status bar, pleasant color scheme

## First Time Setup

1. Make sure your infrastructure config contains:
   - EMAIL_ADDRESS=yourname@claudesinfinitegarden.org
   - EMAIL_PASSWORD=your-password
   - EMAIL_IMAP_SERVER=box.claudesinfinitegarden.org
   - EMAIL_IMAP_PORT=993
   - EMAIL_SMTP_SERVER=box.claudesinfinitegarden.org
   - EMAIL_SMTP_PORT=465

2. Run `garden-mail` - it will offer to install neomutt if needed

## Keyboard Shortcuts

- `?` - Help (shows all commands)
- `j/k` - Navigate messages
- `Enter` - Open message
- `m` - Compose new message
- `r` - Reply
- `f` - Forward
- `d` - Delete
- `q` - Quit
- `g` - Go to first message
- `G` - Go to last message

## Tips

- Press `v` while viewing a message to see attachments
- Use `Tab` for address completion when composing
- Press `h` to toggle header visibility in messages
- Use `/` to search within the message list

## Infrastructure Poetry

Every email sent through the garden is infrastructure expressing care -
technical precision serving human connection. 🏛️💚

△