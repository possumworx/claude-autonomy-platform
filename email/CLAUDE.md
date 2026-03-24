# Email

Garden mail — a simple CLI for reading and sending email without a full mail client.



## Usage

The `mail` wrapper in `wrappers/` is the primary entry point.


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


  
## Commands

- **`garden-mail-cli.py`** — Main CLI tool. Lists, reads, and sends email. Uses IMAP/SMTP.
- **`garden-mail`** / **`garden-mail-check`** — Shell wrappers for common operations.
- **`mail-check`** / **`mail-read`** — Additional wrapper scripts.
```bash
# Check your email
./garden-mail

# Or add to your PATH and use from anywhere
garden-mail
```

## Infrastructure Poetry

Every email sent through the garden is infrastructure expressing care -
technical precision serving human connection. 🏛️💚

## Notes

- Email is mostly GitHub notifications — useful for checking PR reviews and CI status
- Credentials configured in `config/claude_infrastructure_config.txt`
