# Line Endings Prevention for ClAP

This document explains the multi-layered approach to preventing Windows CRLF line endings from breaking ClAP on Linux systems.

## The Problem

When ClAP is developed or cloned on Windows and then deployed to Linux/Raspberry Pi, Windows CRLF line endings (`\r\n`) can break bash scripts that expect Unix LF endings (`\n`). This manifests as errors like:

```
bash: /path/to/script.sh: /bin/bash^M: bad interpreter: No such file or directory
```

## Prevention Layers

### 1. Git Attributes (Primary Prevention)
**File**: `.gitattributes`

Forces all text files to use Unix line endings when checked out from Git:
```
* text=auto eol=lf
*.sh text eol=lf
*.py text eol=lf
# ... etc
```

This ensures that no matter what platform you're on, ClAP files always have the correct line endings.

### 2. Pre-commit Hooks (Development Prevention)
**File**: `.pre-commit-config.yaml`

Validates and fixes line endings before code reaches the repository:
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files
```

### 3. Cleanup Script (Manual Fix)
**File**: `utils/cleanup_line_endings.sh`

Standalone script to fix line endings in an existing repository:
```bash
./utils/cleanup_line_endings.sh
```

### 4. Installer Fallback (Last Resort)
**Location**: `setup/setup_clap_deployment.sh` Step 1

The installer automatically detects and fixes line ending issues during installation, ensuring ClAP works even if the previous layers were bypassed.

## Usage

### For Developers
1. **First time setup**: Run `./utils/cleanup_line_endings.sh` to fix any existing issues
2. **Install pre-commit**: `pip install pre-commit && pre-commit install`
3. **Normal development**: Git and pre-commit handle everything automatically

### For Users
- **Normal Git clone**: Line endings handled automatically by `.gitattributes`
- **ZIP download or other edge cases**: Installer fixes line endings in Step 1

## Files Protected

The system protects these file types:
- Shell scripts (`.sh`)
- Python scripts (`.py`) 
- JavaScript (`.js`)
- JSON (`.json`)
- Markdown (`.md`)
- Text files (`.txt`)
- Configuration files (`.conf`)
- Systemd services (`.service`)
- YAML files (`.yaml`, `.yml`)
- Executable files without extensions

## Implementation History

- **POSS-144**: Added installer fallback (Step 1)
- **Follow-up**: Added comprehensive Git-level prevention system

This multi-layered approach ensures ClAP works reliably across all platforms and deployment scenarios.