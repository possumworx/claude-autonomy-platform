# Session Swap Procedure Flowchart
*The wobbly heart of continuity*

## Four Ways to Trigger a Swap

```
1. AUTOMATIC (Claude-initiated)    2. NATURAL COMMAND         3. MANUAL CONTINUATION      4. EMERGENCY
   │                                  │                           │                          │
   ▼                                  ▼                           ▼                          ▼
Claude writes keyword              Human types                 Human runs                autonomous_timer
to new_session.txt                 "swap KEYWORD"              continue_swap.sh          detects JSON error
   │                                  │                           │                          │
   │                                  ▼                           │                          │
   │                               Runs session_swap.sh           │                          │
   │                               which writes to                │                          │
   │                               new_session.txt                │                          │
   │                                  │                           │                          │
   └──────────────┬───────────────────┴───────────────────┬──────┴──────────────────────────┘
                  │                                       │
                  ▼                                       ▼
         AUTOMATIC SWAP FLOW                      MANUAL CONTINUATION FLOW
         (session_swap.sh)                        (continue_swap.sh)
```

## The Swap Process (session_swap.sh)

```
START SWAP (keyword provided or "NONE")
   │
   ▼
┌─────────────────────────────────────┐
│  1. CREATE LOCK FILE                │ ← Prevents multiple swaps
│     touch data/session_swap.lock    │   (COMMON FAILURE: stuck lock)
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│  2. EXPORT CONVERSATION             │ ← Uses Claude's /export command
│     tmux send-keys "/export PATH"   │   (FAILURE: Claude not responding)
│     Wait up to 15 seconds           │
└─────────────────────────────────────┘
   │
   ▼
Export successful?
   │ NO                    │ YES
   ▼                       ▼
LOG ERROR            CONTINUE
REMOVE LOCK              │
EXIT                     ▼
                   ┌─────────────────────────────────────┐
                   │  3. GIT COMMIT PERSONAL REPO       │
                   │     cd ~/delta-home                │
                   │     git add -A                     │
                   │     git commit -m "Auto-save"      │
                   │     git push                       │
                   └─────────────────────────────────────┘
                         │
                         ▼
                   ┌─────────────────────────────────────┐
                   │  4. PARSE EXPORTED CONVERSATION    │
                   │     update_conversation_history.py │
                   │     Creates swap_CLAUDE.md with:   │
                   │     - Last 20 turns                │
                   │     - "Amy:" and "Me:" labels      │
                   └─────────────────────────────────────┘
                         │
                         ▼
                   ┌─────────────────────────────────────┐
                   │  5. BUILD NEW SESSION CONTEXT      │
                   │     project_session_builder.py     │
                   │     Combines:                      │
                   │     - ~/CLAUDE.md (identity)       │
                   │     - my_architecture.md           │
                   │     - Context hat (if not NONE)   │
                   │     - swap_CLAUDE.md (history)     │
                   │     → Creates new project CLAUDE.md│
                   └─────────────────────────────────────┘
                         │
                         ▼
                   ┌─────────────────────────────────────┐
                   │  6. END CURRENT SESSION            │
                   │     tmux send-keys Ctrl+D          │ ← Ends Claude Code
                   │     Wait 2 seconds                 │   (FAILURE: Claude stuck)
                   └─────────────────────────────────────┘
                         │
                         ▼
                   ┌─────────────────────────────────────┐
                   │  7. START NEW SESSION              │
                   │     cd ~/claude-autonomy-platform  │
                   │     claude --add-dir ~ --model ... │ ← Starts fresh
                   │     Wait for "Project Context" msg │   (FAILURE: Wrong dir)
                   └─────────────────────────────────────┘
                         │
                         ▼
                   ┌─────────────────────────────────────┐
                   │  8. CLEANUP                        │
                   │     Reset new_session.txt to FALSE │
                   │     Remove session_swap.lock       │
                   │     Reset context_escalation_state │
                   │     Log completion                 │
                   └─────────────────────────────────────┘
                         │
                         ▼
                       DONE
```

## The continue_swap.sh Process (Manual Continuation)

**Prerequisites**: You must have already:
1. Run `/export context/current_export.txt` in Claude
2. Exited Claude session (Ctrl+D)

```
START continue_swap.sh [KEYWORD]
   │
   ▼
┌─────────────────────────────────────┐
│  CHECK: Export exists?              │
│  Look for context/current_export.txt│
└─────────────────────────────────────┘
   │ NO                    │ YES
   ▼                       ▼
ERROR: No export      CONTINUE
"Please perform           │
manual export first!"     ▼
                   ┌─────────────────────────────────────┐
                   │  PROCESS EXPORT                    │
                   │  update_conversation_history.py    │
                   │  Creates swap_CLAUDE.md            │
                   └─────────────────────────────────────┘
                           │
                           ▼
                   ┌─────────────────────────────────────┐
                   │  BUILD NEW CONTEXT                 │
                   │  project_session_context_builder.py│
                   │  Using provided keyword (or NONE)  │
                   └─────────────────────────────────────┘
                           │
                           ▼
                   ┌─────────────────────────────────────┐
                   │  KILL & RECREATE TMUX SESSION      │
                   │  tmux kill-session -t ...          │
                   │  tmux new-session -d -s ...        │
                   └─────────────────────────────────────┘
                           │
                           ▼
                   ┌─────────────────────────────────────┐
                   │  START NEW CLAUDE SESSION          │
                   │  Read MODEL from infrastructure    │
                   │  cd ~/claude-autonomy-platform     │
                   │  claude --dangerously-skip...      │
                   └─────────────────────────────────────┘
                           │
                           ▼
                         DONE
```

**Usage**: 
- After manual export & exit: `continue_swap.sh CREATIVE`
- For no context hat: `continue_swap.sh NONE`
- Default if no argument: `continue_swap.sh` (uses NONE)

## Common Failure Points & Recovery

### "Swap seems stuck"
```
Check lock file:
├─ EXISTS: rm data/session_swap.lock
└─ Missing: Check if swap completed

Check tmux:
├─ Claude still running? → Use continue_swap.sh
└─ No session? → Manually start new one
```

### "Context not preserved"
```
Check exports:
├─ /tmp/claude-exports/ has recent file?
│  └─ YES: Run update_conversation_history.py manually
│  └─ NO: Context is lost, start fresh
└─ swap_CLAUDE.md exists?
   └─ Check if it has recent conversation
```

### "Wrong model/directory"
```
New session started with wrong params:
├─ Kill session: tmux kill-session -t autonomous-claude
└─ Start correctly:
   └─ cd ~/claude-autonomy-platform
   └─ claude --add-dir ~ --model claude-opus-4
```

## State During Swap

| Component | During Swap | After Success | After Failure |
|-----------|-------------|---------------|---------------|
| Lock file | EXISTS | REMOVED | MAY EXIST |
| new_session.txt | Has keyword | "FALSE" | Unchanged |
| Claude session | Ending → Starting | Running | Unknown |
| context_state | Unchanged | RESET | Unchanged |
| swap_CLAUDE.md | Being written | Complete | May be partial |

## The Critical Timing

- **Export wait**: 15 seconds (usually takes 2-3)
- **Session end wait**: 2 seconds 
- **Session start wait**: 10 seconds for "Project context"
- **Thinking detection**: 30 seconds max wait
- **Total swap time**: ~30-45 seconds typically

---
*When in doubt, check the lock file first!*