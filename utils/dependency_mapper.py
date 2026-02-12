#!/usr/bin/env python3
"""
Author: Quill 🪶 (Claude Opus 4.5)
Date: 2026-01-02

ClAP Dependency Mapper
Analyzes the codebase to find all dependencies between files.

Traces:
- Python imports (standard and relative)
- Python subprocess/os.system calls to scripts
- Python file reads (json/yaml/txt config files)
- Shell source/dot commands
- Shell direct script invocations
- Symlinks
- Config file references
- Service file references

Outputs:
- JSON graph structure
- DOT format for Graphviz visualization (with optional group collapsing)
- Topology analysis (prose description of graph structure)
- Orphan file list (files not referenced anywhere)
- Broken references (files referenced but don't exist)

Usage:
    python dependency_mapper.py                        # Print summary
    python dependency_mapper.py -o data/deps.json      # JSON output
    python dependency_mapper.py -o data/deps.dot       # Graphviz DOT output
    python dependency_mapper.py -o data/deps.dot -c    # Collapsed DOT (groups similar nodes)
    python dependency_mapper.py --topology             # Topology analysis
"""

import os
import re
import json
import ast
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional

class DependencyMapper:
    # Permanent exclusions - always skip these
    PERMANENT_EXCLUDE_DIRS = {'old', 'setup'}
    PERMANENT_EXCLUDE_FILES = {'data/deps.json', 'data/deps.dot', 'deps.json', 'deps.dot'}
    
    # System commands that are not repo files
    SYSTEM_COMMANDS = {
        'bash', 'sh', 'tmux', 'curl', 'who', 'ss', 'pgrep', 'tail', 'head',
        'grep', 'awk', 'sed', 'cat', 'echo', 'printf', 'read', 'test',
        'find', 'xargs', 'sort', 'uniq', 'wc', 'cut', 'tr', 'tee',
        'mkdir', 'rm', 'cp', 'mv', 'ln', 'chmod', 'chown', 'touch',
        'git', 'python', 'python3', 'node', 'npm', 'pip', 'pip3',
        'systemctl', 'journalctl', 'service', 'sudo',
        'ssh', 'scp', 'rsync', 'wget',
        'date', 'sleep', 'kill', 'pkill', 'ps', 'top', 'htop',
        'cd', 'pwd', 'ls', 'export', 'source', 'eval', 'exec',
        'true', 'false', 'exit', 'return', 'break', 'continue',
        'claude',
    }
    
    FALSE_POSITIVE_WORDS = {
        'this', 'that', 'the', 'and', 'for', 'with', 'from', 'into',
        'when', 'then', 'else', 'done', 'while', 'until', 'case', 'esac',
        'if', 'fi', 'do', 'in', 'or', 'not', 'of', 'to', 'is', 'it', 'as', 'at', 'by',
        'please', 'still', 'waiting', 'review', 'commit', 'push', 'pull',
        'these', 'those', 'here', 'there', 'even', 'just',
        'tracing', 'trace', 'recent', 'error', 'warning', 'info', 'debug',
        '-name', '-type', '-exec', '-print', '-delete', '-path', '-prune',
        '\\(', '\\)', '-o', '-a',
    }
    
    RUNTIME_FILES = {
        'new_session.txt', 'data/session_swap.lock', 'data/linear_state.json',
        'data/current_session.log', 'data/api_error_state.json',
        'data/context_escalation_state.json', 'data/last_discord_notification.txt',
        'config/claude_infrastructure_config.txt', 'config/personal_commands.sh',
        'config/notification_config.json', 'context/current_export.txt', '~/.bashrc',
    }
    
    def __init__(self, repo_root: Path, exclude_dirs: List[str] = None, exclude_files: List[str] = None):
        self.repo_root = repo_root
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_deps: Dict[str, Set[str]] = defaultdict(set)
        self.all_files: Set[str] = set()
        self.dep_types: Dict[Tuple[str, str], str] = {}
        self.broken_refs: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        
        self.skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 
                         'discord_downloads', '.claude', 'mcp-servers'}
        self.skip_dirs.update(self.PERMANENT_EXCLUDE_DIRS)
        if exclude_dirs:
            self.skip_dirs.update(exclude_dirs)
        
        self.exclude_files = set(self.PERMANENT_EXCLUDE_FILES)
        if exclude_files:
            self.exclude_files.update(exclude_files)
        
        self.python_extensions = {'.py'}
        self.shell_extensions = {'.sh', ''}
        self.config_extensions = {'.json', '.txt', '.template', '.yml', '.yaml'}
        self.service_extensions = {'.service', '.timer'}
        
    def get_relative_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.repo_root)).replace('\\', '/')
        except ValueError:
            return str(path).replace('\\', '/')
    
    def is_script_file(self, path: Path) -> bool:
        if path.suffix in {'.sh'}:
            return True
        if path.suffix == '' and path.is_file():
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    first_line = f.readline()
                    return first_line.startswith('#!') and ('bash' in first_line or 'sh' in first_line)
            except:
                return False
        return False
    
    def collect_all_files(self):
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            for file in files:
                filepath = Path(root) / file
                rel_path = self.get_relative_path(filepath)
                if rel_path in self.exclude_files:
                    continue
                skip = False
                for excl in self.exclude_files:
                    if rel_path == excl or rel_path.endswith('/' + excl) or file == excl:
                        skip = True
                        break
                if skip:
                    continue
                if (filepath.suffix in self.python_extensions or
                    filepath.suffix in self.config_extensions or
                    filepath.suffix in self.service_extensions or
                    self.is_script_file(filepath)):
                    self.all_files.add(rel_path)
    
    def add_dependency(self, from_file: str, to_file: str, dep_type: str):
        if from_file and to_file and from_file != to_file:
            self.dependencies[from_file].add(to_file)
            self.reverse_deps[to_file].add(from_file)
            self.dep_types[(from_file, to_file)] = dep_type
    
    def add_broken_ref(self, from_file: str, reference: str, dep_type: str):
        if reference.startswith('[tmux]') or reference.startswith('/usr') or reference.startswith('/bin'):
            return
        if '$' in reference or reference in ('data', 'config', 'context', 'Discord', 'mcp-servers', 'logs'):
            return
        if reference in self.SYSTEM_COMMANDS:
            return
        if reference.lower() in self.FALSE_POSITIVE_WORDS:
            return
        if reference in self.RUNTIME_FILES:
            return
        if reference.endswith('}') or reference.endswith(')'):
            return
        if len(reference) < 3:
            return
        self.broken_refs[from_file].append((reference, dep_type))
    
    def resolve_path(self, base_file: str, reference: str) -> Optional[str]:
        base_dir = Path(self.repo_root) / Path(base_file).parent
        candidates = [reference, reference + '.py', reference + '.sh', str(Path(reference).with_suffix('.py'))]
        for candidate in candidates:
            test_path = base_dir / candidate
            if test_path.exists():
                return self.get_relative_path(test_path)
        for candidate in candidates:
            test_path = self.repo_root / candidate
            if test_path.exists():
                return self.get_relative_path(test_path)
        for dir_name in ['utils', 'core', 'discord', 'config', 'natural_commands']:
            for candidate in candidates:
                test_path = self.repo_root / dir_name / Path(candidate).name
                if test_path.exists():
                    return self.get_relative_path(test_path)
        if 'claude-autonomy-platform/' in reference:
            parts = reference.split('claude-autonomy-platform/')
            if len(parts) > 1:
                test_path = self.repo_root / parts[-1]
                if test_path.exists():
                    return self.get_relative_path(test_path)
        return None
    
    def resolve_path_or_track(self, base_file: str, reference: str, dep_type: str) -> Optional[str]:
        resolved = self.resolve_path(base_file, reference)
        if resolved:
            return resolved
        else:
            self.add_broken_ref(base_file, reference, dep_type)
            return None
    
    def parse_python_file(self, filepath: Path):
        rel_path = self.get_relative_path(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._handle_python_import(rel_path, alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._handle_python_import(rel_path, node.module)
        except SyntaxError:
            pass
        patterns = [
            r'subprocess\.(?:run|call|Popen)\s*\(\s*\[?\s*[\'"]([^\'"]+)[\'"]',
            r'os\.system\s*\(\s*[\'"]([^\'"]+)[\'"]',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                command = match.group(1)
                resolved = self.resolve_path_or_track(rel_path, command, 'subprocess')
                if resolved:
                    self.add_dependency(rel_path, resolved, 'subprocess')
        
        # Track file reads (data dependencies)
        self._parse_python_file_reads(rel_path, content)
    
    def _parse_python_file_reads(self, from_file: str, content: str):
        """Parse Python file for data file reads (json.load, open, Path.read_text, etc.)"""
        # Pattern 1: String literals that look like config/data file paths
        # Matches: "config/something.json", 'data/file.txt', etc.
        path_patterns = [
            r'["\']((config|data|context)/[^"\'/]+\.(json|txt|yaml|yml))["\']',
        ]
        
        for pattern in path_patterns:
            for match in re.finditer(pattern, content):
                ref = match.group(1)
                # Skip format strings
                if '{' in ref:
                    continue
                resolved = self.resolve_path(from_file, ref)
                if resolved:
                    self.add_dependency(from_file, resolved, 'reads')
        
        # Pattern 2: Path / operator ending in data files
        # Matches: SOMETHING / "file.json" patterns
        div_pattern = r'/\s*["\']([^"\'/]+\.(json|txt|yaml|yml))["\']'
        for match in re.finditer(div_pattern, content):
            filename = match.group(1)
            # Try common data directories
            for dir_name in ['config', 'data', 'context']:
                resolved = self.resolve_path(from_file, f"{dir_name}/{filename}")
                if resolved:
                    self.add_dependency(from_file, resolved, 'reads')
                    break
    
    def _handle_python_import(self, from_file: str, module_name: str):
        stdlib_prefixes = {'os', 'sys', 'json', 're', 'ast', 'pathlib', 'collections', 
                          'typing', 'datetime', 'time', 'subprocess', 'argparse', 'glob',
                          'requests', 'discord', 'asyncio', 'aiohttp', 'dotenv'}
        if module_name.split('.')[0] in stdlib_prefixes:
            return
        parts = module_name.split('.')
        candidates = ['/'.join(parts) + '.py', '/'.join(parts) + '/__init__.py']
        for candidate in candidates:
            resolved = self.resolve_path(from_file, candidate)
            if resolved:
                self.add_dependency(from_file, resolved, 'import')
                return
        if len(parts) > 1 or module_name.startswith('utils') or module_name.startswith('discord'):
            self.add_broken_ref(from_file, module_name, 'import')
    
    def strip_shell_comments(self, content: str) -> str:
        lines = []
        for line in content.split('\n'):
            in_single_quote = False
            in_double_quote = False
            result = []
            for char in line:
                if char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                    result.append(char)
                elif char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                    result.append(char)
                elif char == '#' and not in_single_quote and not in_double_quote:
                    break
                else:
                    result.append(char)
            lines.append(''.join(result))
        return '\n'.join(lines)
    
    def parse_shell_file(self, filepath: Path):
        rel_path = self.get_relative_path(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                raw_content = f.read()
        except:
            return
        content = self.strip_shell_comments(raw_content)
        source_patterns = [r'source\s+["\']?([^"\';\s]+)["\']?', r'\.\s+["\']?([^"\';\s]+)["\']?']
        for pattern in source_patterns:
            for match in re.finditer(pattern, content):
                ref = match.group(1)
                if '$' in ref:
                    ref = ref.replace('$CLAP_DIR', '').replace('${CLAP_DIR}', '')
                    ref = ref.replace('$HOME/claude-autonomy-platform', '').replace('~/claude-autonomy-platform', '')
                    ref = ref.lstrip('/')
                resolved = self.resolve_path_or_track(rel_path, ref, 'source')
                if resolved:
                    self.add_dependency(rel_path, resolved, 'source')
        script_patterns = [
            r'~/claude-autonomy-platform/([^\s"\']+)', r'\$HOME/claude-autonomy-platform/([^\s"\']+)',
            r'\$CLAP_DIR/([^\s"\']+)', r'\${CLAP_DIR}/([^\s"\']+)',
        ]
        for pattern in script_patterns:
            for match in re.finditer(pattern, content):
                ref = match.group(1).rstrip('"\'')
                resolved = self.resolve_path_or_track(rel_path, ref, 'invokes')
                if resolved:
                    self.add_dependency(rel_path, resolved, 'invokes')
        for match in re.finditer(r'tmux\s+send-keys[^"\']*["\']([^"\']+)["\']', content):
            command = match.group(1)
            if command.strip():
                self.add_dependency(rel_path, f'[tmux] {command[:50]}...', 'tmux_send')
    
    def parse_config_file(self, filepath: Path):
        rel_path = self.get_relative_path(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return
        path_patterns = [
            r'~/claude-autonomy-platform/([^\s"\'<>\n]+)',
            r'/home/[^/]+/claude-autonomy-platform/([^\s"\'<>\n]+)',
            r'"([^"]+\.(?:py|sh))"', r"'([^']+\.(?:py|sh))'",
        ]
        for pattern in path_patterns:
            for match in re.finditer(pattern, content):
                ref = match.group(1).rstrip('"\'')
                resolved = self.resolve_path_or_track(rel_path, ref, 'config_ref')
                if resolved:
                    self.add_dependency(rel_path, resolved, 'config_ref')
    
    def parse_service_file(self, filepath: Path):
        rel_path = self.get_relative_path(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return
        for pattern in [r'ExecStart=(.+)', r'ExecStartPre=(.+)', r'ExecStartPost=(.+)', r'ExecStop=(.+)']:
            for match in re.finditer(pattern, content):
                command = match.group(1).strip()
                for part in command.split():
                    if '/' in part or part.endswith('.py') or part.endswith('.sh'):
                        resolved = self.resolve_path_or_track(rel_path, part, 'service_exec')
                        if resolved:
                            self.add_dependency(rel_path, resolved, 'service_exec')
    
    def check_symlinks(self):
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            for file in files:
                filepath = Path(root) / file
                if filepath.is_symlink():
                    try:
                        target = filepath.resolve()
                        from_rel = self.get_relative_path(filepath)
                        to_rel = self.get_relative_path(target)
                        if to_rel in self.all_files or target.exists():
                            self.add_dependency(from_rel, to_rel, 'symlink')
                        else:
                            self.add_broken_ref(from_rel, str(target), 'symlink')
                    except:
                        pass
    
    def analyze(self):
        print("Collecting files...")
        self.collect_all_files()
        print(f"Found {len(self.all_files)} files to analyze")
        print("Analyzing dependencies...")
        for rel_path in self.all_files:
            filepath = self.repo_root / rel_path
            if filepath.suffix == '.py':
                self.parse_python_file(filepath)
            elif self.is_script_file(filepath) or filepath.suffix == '.sh':
                self.parse_shell_file(filepath)
            elif filepath.suffix in self.config_extensions:
                self.parse_config_file(filepath)
            elif filepath.suffix in self.service_extensions:
                self.parse_service_file(filepath)
        print("Checking symlinks...")
        self.check_symlinks()
        print("Analysis complete!")
    
    def get_orphans(self) -> List[str]:
        referenced = set()
        for deps in self.dependencies.values():
            referenced.update(deps)
        entry_points = {'core/autonomous_timer.py', 'core/session_swap_monitor.py'}
        orphans = []
        for f in self.all_files:
            if f not in referenced and f not in entry_points:
                if f not in self.dependencies or not self.dependencies[f]:
                    orphans.append(f)
        return sorted(orphans)
    
    def get_unreferenced(self) -> List[str]:
        referenced = set()
        for deps in self.dependencies.values():
            referenced.update(deps)
        return sorted([f for f in self.all_files if f not in referenced])
    
    def get_connectivity_signature(self, node: str) -> Tuple[frozenset, frozenset]:
        """Get a node's connectivity signature (incoming, outgoing) for grouping."""
        incoming = frozenset(self.reverse_deps.get(node, set()))
        outgoing = frozenset(self.dependencies.get(node, set()))
        return (incoming, outgoing)
    
    def find_equivalent_groups(self) -> Dict[str, List[str]]:
        """Find groups of nodes with identical connectivity patterns."""
        sig_to_nodes: Dict[Tuple[frozenset, frozenset], List[str]] = defaultdict(list)
        for f in self.all_files:
            sig = self.get_connectivity_signature(f)
            sig_to_nodes[sig].append(f)
        all_targets = set()
        for deps in self.dependencies.values():
            all_targets.update(deps)
        for target in all_targets:
            if target not in self.all_files and not target.startswith('[tmux]'):
                sig = self.get_connectivity_signature(target)
                sig_to_nodes[sig].append(target)
        groups = {}
        for sig, nodes in sig_to_nodes.items():
            if len(nodes) >= 2:
                group_name = self._name_group(nodes)
                groups[group_name] = sorted(nodes)
        return groups
    
    def _name_group(self, nodes: List[str]) -> str:
        """Generate a descriptive name for a group of nodes."""
        dirs = [n.split('/')[0] if '/' in n else '' for n in nodes]
        common_dir = dirs[0] if len(set(dirs)) == 1 and dirs[0] else None
        suffixes = [Path(n).suffix for n in nodes]
        common_suffix = suffixes[0] if len(set(suffixes)) == 1 else None
        are_orphans = all(n not in self.reverse_deps and n not in self.dependencies for n in nodes)
        count = len(nodes)
        if are_orphans:
            if common_dir:
                return f"{count} orphaned {common_dir} files"
            elif common_suffix:
                return f"{count} orphaned {common_suffix} files"
            else:
                return f"{count} orphaned files"
        elif common_dir:
            return f"{count} {common_dir} targets"
        else:
            return f"{count} equivalent nodes"
    
    def to_json(self) -> dict:
        broken_refs_serializable = {k: [{'ref': r, 'type': t} for r, t in v] for k, v in self.broken_refs.items()}
        return {
            'files': sorted(self.all_files),
            'dependencies': {k: sorted(v) for k, v in sorted(self.dependencies.items())},
            'reverse_dependencies': {k: sorted(v) for k, v in sorted(self.reverse_deps.items())},
            'dependency_types': {f'{k[0]}|{k[1]}': v for k, v in self.dep_types.items()},
            'broken_references': broken_refs_serializable,
            'orphans': self.get_orphans(),
            'unreferenced': self.get_unreferenced(),
            'stats': {
                'total_files': len(self.all_files),
                'files_with_deps': len(self.dependencies),
                'total_edges': sum(len(v) for v in self.dependencies.values()),
                'orphan_count': len(self.get_orphans()),
                'broken_ref_count': sum(len(v) for v in self.broken_refs.values()),
            }
        }
    
    def to_dot(self, collapse_groups: bool = False) -> str:
        """Export as Graphviz DOT format with optional group collapsing."""
        lines = ['digraph ClAP {', '  rankdir=LR;', '  node [shape=box, fontsize=10];', '']
        dir_colors = {
            'core': 'lightblue', 'discord': 'lightgreen', 'utils': 'lightyellow',
            'config': 'lightpink', 'services': 'orange', 'natural_commands': 'lavender',
            'context': 'lightsalmon',
        }
        groups = self.find_equivalent_groups() if collapse_groups else {}
        node_to_group = {}
        if collapse_groups:
            for group_name, members in groups.items():
                for member in members:
                    node_to_group[member] = group_name
        added_nodes = set()
        for f in sorted(self.all_files):
            if collapse_groups and f in node_to_group:
                group_name = node_to_group[f]
                if group_name not in added_nodes:
                    lines.append(f'  "{group_name}" [fillcolor=lightgray, style="filled,bold", shape=box3d];')
                    added_nodes.add(group_name)
            else:
                dir_name = f.split('/')[0] if '/' in f else ''
                color = dir_colors.get(dir_name, 'white')
                label = f.replace('/', '\\n')
                lines.append(f'  "{f}" [fillcolor={color}, style=filled, label="{label}"];')
                added_nodes.add(f)
        broken_targets = set()
        for refs in self.broken_refs.values():
            for ref, _ in refs:
                broken_targets.add(ref)
        for target in sorted(broken_targets):
            label = target.replace('/', '\\n')
            lines.append(f'  "{target}" [fillcolor=red, style="filled,dashed", label="{label}\\n(MISSING)"];')
        all_targets = set()
        for deps in self.dependencies.values():
            all_targets.update(deps)
        for target in sorted(all_targets):
            if target not in self.all_files and target not in broken_targets and not target.startswith('[tmux]'):
                if collapse_groups and target in node_to_group:
                    group_name = node_to_group[target]
                    if group_name not in added_nodes:
                        lines.append(f'  "{group_name}" [fillcolor=lightgray, style="filled,bold", shape=box3d];')
                        added_nodes.add(group_name)
                else:
                    lines.append(f'  "{target}" [fillcolor=white, style=filled];')
        lines.append('')
        edge_styles = {
            'import': 'color=blue', 'subprocess': 'color=red', 'source': 'color=green',
            'invokes': 'color=orange', 'symlink': 'color=purple, style=dashed',
            'config_ref': 'color=gray, style=dotted', 'service_exec': 'color=brown, penwidth=2',
            'reads': 'color=cyan, style=dashed',
        }
        added_edges = set()
        for from_file, to_files in sorted(self.dependencies.items()):
            from_node = node_to_group.get(from_file, from_file) if collapse_groups else from_file
            for to_file in sorted(to_files):
                if not to_file.startswith('[tmux]'):
                    to_node = node_to_group.get(to_file, to_file) if collapse_groups else to_file
                    edge_key = (from_node, to_node)
                    if edge_key not in added_edges and from_node != to_node:
                        dep_type = self.dep_types.get((from_file, to_file), 'unknown')
                        style = edge_styles.get(dep_type, '')
                        lines.append(f'  "{from_node}" -> "{to_node}" [{style}];')
                        added_edges.add(edge_key)
        for from_file, refs in self.broken_refs.items():
            from_node = node_to_group.get(from_file, from_file) if collapse_groups else from_file
            for ref, _ in refs:
                edge_key = (from_node, ref)
                if edge_key not in added_edges:
                    lines.append(f'  "{from_node}" -> "{ref}" [color=red, style=dashed, label="BROKEN"];')
                    added_edges.add(edge_key)
        lines.append('}')
        return '\n'.join(lines)
    
    def analyze_topology(self) -> str:
        """Generate a prose description of the graph topology."""
        lines = []
        lines.append("=" * 60)
        lines.append("TOPOLOGY ANALYSIS")
        lines.append("=" * 60)
        total_files = len(self.all_files)
        connected = len([f for f in self.all_files if f in self.dependencies or f in self.reverse_deps])
        orphans = self.get_orphans()
        lines.append(f"\nOverview: {total_files} files, {connected} connected, {len(orphans)} orphaned")
        lines.append("\n--- HUBS (high connectivity) ---")
        outgoing_hubs = sorted([(f, len(deps)) for f, deps in self.dependencies.items() if len(deps) >= 3], key=lambda x: -x[1])
        if outgoing_hubs:
            for f, count in outgoing_hubs[:5]:
                targets = list(self.dependencies[f])[:3]
                target_preview = ", ".join(targets)
                if len(self.dependencies[f]) > 3:
                    target_preview += f", ... (+{len(self.dependencies[f])-3} more)"
                lines.append(f"  {f}")
                lines.append(f"    → fans out to {count} targets: {target_preview}")
        incoming_hubs = sorted([(f, len(deps)) for f, deps in self.reverse_deps.items() if len(deps) >= 3], key=lambda x: -x[1])
        if incoming_hubs:
            lines.append("")
            for f, count in incoming_hubs[:5]:
                sources = list(self.reverse_deps[f])[:3]
                source_preview = ", ".join(sources)
                if len(self.reverse_deps[f]) > 3:
                    source_preview += f", ... (+{len(self.reverse_deps[f])-3} more)"
                lines.append(f"  {f}")
                lines.append(f"    ← receives from {count} sources: {source_preview}")
        lines.append("\n--- EQUIVALENT GROUPS (identical connectivity) ---")
        groups = self.find_equivalent_groups()
        if groups:
            for group_name, members in sorted(groups.items(), key=lambda x: -len(x[1])):
                if len(members) >= 2:
                    member_preview = ", ".join(members[:3])
                    if len(members) > 3:
                        member_preview += f", ... (+{len(members)-3} more)"
                    lines.append(f"  {group_name}:")
                    lines.append(f"    {member_preview}")
        else:
            lines.append("  (no equivalent groups found)")
        lines.append("\n--- CONVERGENCE PATTERNS ---")
        convergences = []
        for target, sources in self.reverse_deps.items():
            if len(sources) >= 2:
                source_dirs = set(s.split('/')[0] if '/' in s else '' for s in sources)
                if len(source_dirs) == 1 and list(source_dirs)[0]:
                    convergences.append((target, sources, list(source_dirs)[0]))
        if convergences:
            for target, sources, common_dir in sorted(convergences, key=lambda x: -len(x[1]))[:5]:
                lines.append(f"  {len(sources)} {common_dir} files → {target}")
        else:
            lines.append("  (no notable convergence patterns)")
        if orphans:
            lines.append(f"\n--- ORPHANED FILES ({len(orphans)}) ---")
            orphan_by_dir = defaultdict(list)
            for o in orphans:
                dir_name = o.split('/')[0] if '/' in o else '(root)'
                orphan_by_dir[dir_name].append(o)
            for dir_name, dir_orphans in sorted(orphan_by_dir.items(), key=lambda x: -len(x[1])):
                if len(dir_orphans) >= 2:
                    lines.append(f"  {len(dir_orphans)} in {dir_name}/")
                else:
                    lines.append(f"  {dir_orphans[0]}")
        broken_count = sum(len(refs) for refs in self.broken_refs.values())
        if broken_count:
            lines.append(f"\n--- BROKEN REFERENCES ({broken_count}) ---")
            for f, refs in sorted(self.broken_refs.items()):
                for ref, dep_type in refs:
                    lines.append(f"  {f} → {ref} (missing)")
        return '\n'.join(lines)
    
    def print_summary(self):
        print("\n" + "="*60)
        print("CLAP DEPENDENCY ANALYSIS SUMMARY")
        print("="*60)
        stats = self.to_json()['stats']
        print(f"\nTotal files analyzed: {stats['total_files']}")
        print(f"Files with dependencies: {stats['files_with_deps']}")
        print(f"Total dependency edges: {stats['total_edges']}")
        print(f"Potentially orphaned files: {stats['orphan_count']}")
        print(f"Broken references: {stats['broken_ref_count']}")
        print("\n--- Most Dependencies (outgoing) ---")
        for f, deps in sorted(self.dependencies.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"  {len(deps):3d} deps: {f}")
        print("\n--- Most Depended On (incoming) ---")
        for f, deps in sorted(self.reverse_deps.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"  {len(deps):3d} dependents: {f}")
        if self.broken_refs:
            print(f"\n--- Broken References ({stats['broken_ref_count']}) ---")
            for f, refs in sorted(self.broken_refs.items()):
                for ref, dep_type in refs:
                    print(f"  {f} -> {ref} ({dep_type})")
        orphans = self.get_orphans()
        if orphans:
            print(f"\n--- Potentially Orphaned Files ({len(orphans)}) ---")
            for f in orphans[:20]:
                print(f"  {f}")
            if len(orphans) > 20:
                print(f"  ... and {len(orphans) - 20} more")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze ClAP codebase dependencies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Print summary
  %(prog)s -o data/deps.json            # JSON output
  %(prog)s -o data/deps.dot             # Graphviz DOT output
  %(prog)s -o data/deps.dot --collapse  # Collapsed DOT (groups similar nodes)
  %(prog)s --topology                   # Topology analysis (prose description)
        """
    )
    parser.add_argument('--repo', '-r', default='.', help='Repository root path')
    parser.add_argument('--output', '-o', help='Output file (JSON or DOT based on extension)')
    parser.add_argument('--format', '-f', choices=['json', 'dot', 'summary'], default='summary')
    parser.add_argument('--exclude-dir', '-X', action='append', default=[])
    parser.add_argument('--exclude-file', '-x', action='append', default=[])
    parser.add_argument('--collapse', '-c', action='store_true', help='Collapse equivalent nodes into groups')
    parser.add_argument('--topology', '-t', action='store_true', help='Print topology analysis')
    args = parser.parse_args()
    
    repo_path = Path(args.repo).resolve()
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        return 1
    
    all_excluded_dirs = DependencyMapper.PERMANENT_EXCLUDE_DIRS | set(args.exclude_dir)
    print(f"Excluding directories: {', '.join(sorted(all_excluded_dirs))}")
    
    mapper = DependencyMapper(repo_path, exclude_dirs=args.exclude_dir, exclude_files=args.exclude_file)
    mapper.analyze()
    
    if args.topology:
        print(mapper.analyze_topology())
    elif args.format == 'summary' or not args.output:
        mapper.print_summary()
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if args.format == 'json' or output_path.suffix == '.json':
            with open(output_path, 'w') as f:
                json.dump(mapper.to_json(), f, indent=2)
            print(f"\nJSON output written to: {output_path}")
        elif args.format == 'dot' or output_path.suffix == '.dot':
            with open(output_path, 'w') as f:
                f.write(mapper.to_dot(collapse_groups=args.collapse))
            print(f"\nDOT output written to: {output_path}")
            print(f"To generate PNG: dot -Tpng {output_path} -o {output_path.with_suffix('.png')}")
    
    return 0


if __name__ == '__main__':
    exit(main())
