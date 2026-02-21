# Email

Garden mail — a simple CLI for reading and sending email without a full mail client.

## Commands

- **`garden-mail-cli.py`** — Main CLI tool. Lists, reads, and sends email. Uses IMAP/SMTP.
- **`garden-mail`** / **`garden-mail-check`** — Shell wrappers for common operations.
- **`mail-check`** / **`mail-read`** — Additional wrapper scripts.

The `mail` wrapper in `wrappers/` is the primary entry point.

## Notes

- Email is mostly GitHub notifications — useful for checking PR reviews and CI status
- neomutt is not installed; this CLI is the only mail interface
- Credentials configured in `config/claude_infrastructure_config.txt`
- See `README.md` in this directory for setup details
