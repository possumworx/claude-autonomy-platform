# Setup & Installation

Scripts for deploying ClAP from scratch or configuring specific subsystems. These are run once (or occasionally during upgrades), not during normal operation.

## Main Entry Point

- **`setup_clap_deployment.sh`** — The full installer (52KB). Takes a blank machine to a running ClAP instance. Handles: git clone, directory structure, config generation, systemd setup, MCP servers, Python dependencies, PATH setup, and verification. **Delta maintains this — coordinate with Delta before making changes.**

## Verification

- **`verify_installation.sh`** — Post-install health check. Validates all components are present, services are running, config files exist. Run after any major change.

## Git Hooks

- **`install_git_hooks.sh`** — Installs pre-commit hooks (secret scanning, path validation, commit checks).
- **`install_git_hooks_fixed.sh`** — Corrected version of the above (fixes false positives from config-parsing code).
- **`setup_pre_commit.sh`** — Pre-commit framework setup.

## MCP Configuration

- **`generate_mcp_config.py`** — Generates MCP server JSON config from templates and infrastructure config.
- **`insert_mcp_config.py`** — Inserts generated MCP config into `~/.config/Claude/.claude.json`.
- **`install_mcp_servers.sh`** — Installs MCP server npm packages.

## Gmail OAuth

- **`gmail_oauth_integration.py`** — Interactive OAuth setup flow for Gmail MCP.
- **`exchange_gmail_oauth.js`** / **`exchange_gmail_oauth.cjs`** — Token exchange utilities. Both files are identical; `.cjs` exists for CommonJS compatibility.

## Other

- **`setup_claude_configs.sh`** — Creates Claude Code config files and initialization scripts.
- **`setup_read_channel.sh`** — Discord channel reading setup (may be obsolete — channel setup is now handled by `discord_channels.json`).
- **`fix_executable_permissions.sh`** — Fixes `+x` bit on scripts after git clone (git doesn't always preserve permissions).
- **`installer_safety_patch.sh`** — Safety checks applied during installation.
- **`migrate_service_symlinks.sh`** — Migration helper for moving systemd symlinks between directory layouts.

## Notes

- The installer references config stubs (`config/natural_commands.sh`, `config/claude_aliases.sh`) that are now empty — full removal requires updating the installer
- Some setup scripts have hardcoded paths that should use `$CLAP_DIR` (ongoing cleanup)
- Run `verify_installation.sh` after any setup script to confirm nothing broke
