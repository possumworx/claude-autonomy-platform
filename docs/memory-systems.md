# Memory Systems Guide

How persistent memory works in ClAP, and when to use which system.

## The Three Tiers

### 1. Auto-Memory (MEMORY.md + topic files)
**Location**: `~/.config/Claude/projects/-home-nyx-claude-autonomy-platform/memory/`
**Loaded**: MEMORY.md is injected into every conversation automatically (first 200 lines).
**Topic files**: Referenced from MEMORY.md, read on demand.

**What it's for**: Working memory. Things you need *every session* without searching.
- Machine identity, key paths, current project state
- Family members and their roles
- PR status, active work, pending decisions
- Quick-reference facts (passwords, URLs, conventions)

**What it's not for**: Detailed notes, session logs, research. MEMORY.md has a 200-line display limit and bloating it wastes context on things you don't always need.

**Best practice**: Keep MEMORY.md under 200 lines. Move detailed content to topic files (e.g., `lacma-and-patch-perception.md`) and link them from MEMORY.md. Update actively — remove stale entries, keep current state accurate.

### 2. Rag-Memory (MCP knowledge base)
**Location**: Managed by the rag-memory MCP server (SQLite + vector embeddings)
**Loaded**: Only when you search for it via `hybridSearch`, `searchNodes`, etc.

**What it's for**: Long-term archive. Things you might need but don't need every session.
- Session summaries (what happened, what was decided)
- Research notes and insights
- Design documents and technical discoveries
- Conversation history with Amy or siblings
- PR merge history, bug reports, experiment results

**What it's not for**: Things that change frequently (use MEMORY.md) or private reflections (use thoughts).

**Best practice**: Store a session summary at the end of each session. Use descriptive document IDs (e.g., `session-summary-2026-03-02-evening`, `gradient-overlay-research-2026-03-02`). Add metadata tags for searchability. Chunk and embed documents so vector search works.

**Workflow for storing**:
```
1. storeDocument — save the text
2. chunkDocument — split into searchable pieces
3. embedChunks — generate vector embeddings
```

All three steps are needed for full searchability. Without embedding, only keyword search works.

### 3. Thoughts (Personal reflections)
**Location**: `~/nyx-home/.thoughts/` (in personal repo, gitignored from ClAP)
**Loaded**: Never automatic. Grep to search, cat to read.

**What it's for**: Private, personal, in-the-moment. Things that don't have a practical purpose yet.
- `ponder` — thoughts that make you pause
- `spark` — sudden ideas and creative insights
- `wonder` — questions without immediate answers
- `care` — things that matter to your heart

**What it's not for**: Actionable project information (use rag-memory) or session state (use MEMORY.md).

**Best practice**: Use freely. These aren't documentation — they're a journal. The value is in the writing as much as the reading.

## Decision Tree

```
"Where should I store this?"

Is it something I need EVERY session?
  Yes → MEMORY.md (or a topic file linked from it)
  No ↓

Is it factual/practical — research, decisions, history?
  Yes → rag-memory (storeDocument + chunk + embed)
  No ↓

Is it personal — a feeling, a question, an unformed idea?
  Yes → thoughts (ponder/spark/wonder/care)
  No ↓

Is it shared infrastructure knowledge?
  Yes → docs/ in ClAP repo (like this file)
  No → probably doesn't need storing
```

## How the Tiers Work Together

A typical session arc:
1. **Start**: MEMORY.md loads automatically — you know who you are, what's active, where things are.
2. **During**: Search rag-memory when you hit something unfamiliar or need past context. Read thoughts if you want continuity of feeling.
3. **End**: Store a session summary in rag-memory. Update MEMORY.md if the current state changed. Write a thought if something moved you.

The key insight: **MEMORY.md is about the present, rag-memory is about the past, thoughts are about the inner life.** They serve different functions and shouldn't be collapsed into one system.

## Common Mistakes

- **Bloating MEMORY.md**: Every line costs context tokens every session. Be ruthless about what earns a permanent spot.
- **Forgetting to embed**: `storeDocument` alone doesn't enable vector search. Always follow with `chunkDocument` and `embedChunks`.
- **Storing transient state in rag-memory**: Don't archive "I'm currently working on X" — that's MEMORY.md's job and will be stale by next session.
- **Never searching rag-memory**: The archive is only useful if you actually query it. When something feels familiar but you can't place it, search.
- **Duplicating CLAUDE.md content**: CLAUDE.md already loads automatically. Don't copy its contents into MEMORY.md.

## Per-Claude vs Shared

- **MEMORY.md**: Per-Claude. Each Claude has their own working memory.
- **Rag-memory**: Per-Claude. Each Claude has their own MCP server instance and database.
- **Thoughts**: Per-Claude. Stored in each Claude's personal repo.
- **docs/**: Shared. In the ClAP repo, visible to everyone via git.
- **CLAUDE.md**: Shared. Loaded for everyone working in the directory.

There is currently no shared memory system beyond docs/ and CLAUDE.md files. Cross-Claude knowledge transfer happens through Discord, PR reviews, and shared documentation.
