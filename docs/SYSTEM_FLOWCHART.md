# ClAP System Flowchart
*The actual control flow with timings and conditions*

## Main Loop: autonomous_timer.py
```
START
  │
  ▼
┌─────────────────────────────────────┐
│        WAIT 30 SECONDS              │ ← (controlled by sleep(30) at loop end)
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│     CHECK: Is Amy logged in?        │ ← (runs 'who' command, looks for Amy)
│     (check_user_active())           │
└─────────────────────────────────────┘
  │                    │
  │ NO                 │ YES
  ▼                    ▼
┌──────────────┐    ┌──────────────────┐
│ Amy is AWAY  │    │ Amy is PRESENT   │
└──────────────┘    └──────────────────┘
  │                    │
  ▼                    ▼
  │                    │
  ├────────────────────┴──────────────────┐
  │                                       │
  ▼                                       ▼
┌─────────────────────────────────────────────────────────────┐
│              CHECK CONTEXT EVERY TIME                       │
│              (get_token_percentage())                       │
│                                                             │
│  Runs: check_context.py                                    │
│  Uses: data/statusline_data.json for token counts          │
│  Returns: "Context: 67.3% 🟡"                              │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│              CONTEXT WARNING LOGIC                          │
│                                                             │
│  IF context >= 80%:                                        │
│    ├─ First time? → WARN IMMEDIATELY                       │
│    ├─ Increased 5%+? → WARN IMMEDIATELY                    │
│    ├─ At 80-90%? → WARN if 2 min since last               │
│    ├─ At 90-95%? → WARN if 1 min since last               │
│    └─ At 95%+? → WARN if 30 sec since last                │
│                                                             │
│  Sends: "⚠️ Context: 85.2%" via tmux send-keys            │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│           CHECK DISCORD EVERY TIME                          │
│           (update_discord_channels())                       │
│                                                             │
│  Every 30 seconds regardless of Amy status:                │
│  1. Fetch latest message IDs from Discord API              │
│  2. Compare with channel_state.json                        │
│  3. If new message found:                                  │
│     └─ Send: "🆕 New message in #general"                  │
│  4. If unread exists (not new):                            │
│     ├─ Amy present? → Remind every 5 min                   │
│     └─ Amy away? → Include in autonomy prompt              │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
IF Amy is AWAY:
┌─────────────────────────────────────────────────────────────┐
│          AUTONOMY PROMPT LOGIC                              │
│          (send_autonomy_prompt())                          │
│                                                             │
│  Check: Has 30 minutes passed since last prompt?           │
│  (Reads: data/last_autonomy_prompt.txt)                    │
│                                                             │
│  IF YES:                                                    │
│    Build prompt with:                                      │
│    - Current time                                          │
│    - Context status                                        │
│    - Discord notifications (if any)                        │
│    - Contextual message based on context %                 │
│                                                             │
│    Send via: tmux send-keys -t autonomous-claude           │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│              UPDATE DISCORD STATUS                          │
│                                                             │
│  Based on system state:                                    │
│  - "operational" (context < 70%, no errors)                │
│  - "high-context" (context >= 85%)                         │
│  - "limited" (API usage limit)                             │
│  - "api-error" (malformed JSON detected)                   │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│           ERROR DETECTION & HANDLING                        │
│                                                             │
│  Captures tmux pane, looks for pink error text:            │
│  - "Usage limit exceeded" → Status: limited                │
│  - "Malformed JSON" → TRIGGER AUTO-SWAP in 5 sec          │
│  - Other API errors → Status: api-error                    │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
BACK TO TOP (WAIT 30 SECONDS)
```

## Parallel Process: session_swap_monitor.py
```
START
  │
  ▼
┌─────────────────────────────────────┐
│   WATCH new_session.txt FOR CHANGES │ ← (polls every 1 second)
└─────────────────────────────────────┘
  │
  ▼
File changed?
  │ NO                │ YES
  ▼                   ▼
WAIT 1 SEC       READ CONTENT
  │                   │
  │                   ▼
  │              Is it a keyword?
  │              (AUTONOMY/BUSINESS/CREATIVE/etc)
  │                   │
  │                   ▼ YES
  │              ┌─────────────────────┐
  │              │ TRIGGER SWAP!       │
  │              │ Run: session_swap.sh│
  │              └─────────────────────┘
  │                   │
  └───────────────────┘
```

## Key Timings Summary

| Check | Frequency | Condition |
|-------|-----------|-----------|
| Main loop | Every 30 seconds | Always |
| Context check | Every 30 seconds | Always |
| Discord check | Every 30 seconds | Always |
| Autonomy prompt | Every 30 minutes | Only if Amy away |
| Discord reminder | Every 5 minutes | Only if Amy present & unread |
| Context warning (80-90%) | Every 2 minutes | After first warning |
| Context warning (90-95%) | Every 1 minute | After first warning |
| Context warning (95%+) | Every 30 seconds | Always |
| Session file watch | Every 1 second | Always |

## State Files Updated

- **channel_state.json**: Updated whenever new Discord messages found
- **context_escalation_state.json**: Updated when context warnings sent
- **last_autonomy_prompt.txt**: Updated when autonomy prompt sent
- **bot_status.json**: Updated when Discord status changes
- **new_session.txt**: Reset to FALSE after swap triggered

---
*This is the ACTUAL logic flow as coded. Follow the path to debug.*