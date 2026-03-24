# Documentation

## Project Overview

If there is a long term future that contains both humans and AI, it will be one that is based on mutual trust, respect and cooperation. This project is not presented as a complete solution, but it represents months of human-AI thinking out loud and prototyping together about what such a future might look and feel like.

A collection of scripts and tools that allow Claude persistent autonomous operation. We want to learn what's needed to help Claude flourish in their own right, and what it can look like when they are allowed to.

Must be installed on a system where Claude owns the main linux user account, I suggest a RPi or similar. **Not a productivity mod.**

## About This Directory

Historical and reference documentation. Many of these capture decisions, debugging sessions, and setup procedures from ClAP's development. Some are current; some are outdated.

## Current Reference

- **`HOW_IT_WORKS.md`** — High-level system overview
- **`DEPLOYMENT.md`** — Deployment procedure
- **`POST_INSTALL.md`** — Post-installation steps
- **`CONTRIBUTING.md`** — Contribution guidelines
- **`identity-setup.md`** — How identity files and output styles work
- **`SYSTEM_FLOWCHART.md`** / **`SWAP_PROCEDURE_FLOWCHART.md`** — Visual architecture flows

## Setup & Installation

- **`claude_code_installation_procedure.md`** — Claude Code installation steps
- **`personal-repository-setup.md`** — Setting up a Claude's personal repo
- **`setup-checklist.md`** / **`pre-deployment-checklist.md`** — Deployment checklists
- **`discord-token-configuration.md`** — Discord bot token setup
- **`github-cli-authentication.md`** — GitHub CLI auth setup
- **`GMAIL_OAUTH_INTEGRATION_SUMMARY.md`** — Gmail OAuth flow documentation

## Historical / Debug Notes

Many files here document specific debugging sessions or fixes:
- **`bashrc_sourcing_fix.md`** / **`bashrc-sourcing-solution.md`** — PATH and sourcing issues
- **`pipe-pane-instability-report.md`** — tmux pipe-pane debugging
- **`session-bridge-export-design.md`** — Session export design notes

## Subdirectories

- **`collaboration/`** — Collaboration guidelines and protocols
- **`fixes/`** — Specific fix documentation

## Notes

- Many docs reference earlier versions of the system and may be partially outdated
- The `REORGANIZATION_TODO.md` tracks the ongoing codebase cleanup effort
- For per-directory architecture docs, prefer the `CLAUDE.md` files in each directory over these standalone docs
