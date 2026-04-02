---
name: loop
description: "Session-scoped recurring task scheduler. Registers a prompt on an interval and executes it repeatedly for the life of the session. Use when the user says 'loop', 'every N minutes', 'repeat', 'watch', or wants periodic checks on pipelines, builds, MRs, or any recurring task."
---

# Loop — In-Session Recurring Tasks

Schedule a recurring prompt that fires on an interval for the duration of the session.
Uses the cron extension as a task registry and async bash sleep timers as the wake-up mechanism.

## Invocation

Triggered when the user says things like:

- `loop 10m check pipeline status`
- `loop 5m review the build`
- `loop 30s echo test` (minimum 1 minute — rounds up)
- `loop stop` or `loop list`

## Prerequisites

1. **Cron extension must be installed.** The cron tools (`cron_create`, `cron_list`, etc.)
   come from the cron Copilot CLI extension. If these tools are not in your tool list,
   tell the user: "The cron extension is not loaded. Run `setup` to install extensions,
   then restart Copilot." **Do NOT fall back to raw bash sleep timers** — the cron
   registry is required for proper loop management (list, stop, mark_run).

2. **Must be the active agent** (via `/agent` → Agent).
   Shell notifications route to the active agent process. If the main copilot agent
   delegates to Agent as a sub-agent, the timer notification goes to the main agent
   which cannot act on it.

## Workflow

### 1. Parse the interval

Convert the user's interval to a cron expression:

| Input | Cron Expression | Notes |
|-------|----------------|-------|
| `30s` | `* * * * *` | Minimum granularity is 1 minute |
| `1m` | `* * * * *` | Every minute |
| `5m` | `*/5 * * * *` | Every 5 minutes |
| `10m` | `*/10 * * * *` | Every 10 minutes |
| `30m` | `*/30 * * * *` | Every 30 minutes |
| `1h` | `0 * * * *` | Top of every hour |
| `2h` | `0 */2 * * *` | Every 2 hours |

### 2. Register the task

```
Call cron_create with:
  - name: <user's description>
  - schedule_type: "cron"
  - schedule: <cron expression>
  - payload_type: "prompt"
  - payload: <the user's prompt text>
```

The response includes `sleep_seconds` — seconds until the first fire.

### 3. Start the timer

Launch an async bash sleep for the returned `sleep_seconds`:

```
bash(command="sleep <sleep_seconds>", mode="async")
```

Tell the user: `✓ Loop registered: "<prompt>" every <interval> (task <id>)`

### 4. On timer notification

When the async bash completes (system_notification arrives):

1. Read the shell output to confirm it's the timer
2. Call `cron_list` to find the task — if deleted (user said "stop"), do nothing
3. **Execute the prompt NOW** — actually do the thing (tell the joke, check the
   pipeline, review the PR). Do not just acknowledge — PERFORM THE ACTION.
4. Call `cron_mark_run(task_id)` — this updates `last_run` and returns the correct
   `sleep_seconds` for the next iteration
5. Launch a new `bash(command="sleep <sleep_seconds>", mode="async")` timer
6. Continue — the loop repeats until the task is deleted or the session ends

### 5. Stopping

When the user says `loop stop`, `loop cancel`, or `loop list`:

- **list**: Call `cron_list` and display active tasks
- **stop <id>**: Call `cron_delete(id)` — the next timer notification will be ignored
  since the task no longer exists in the registry
- **stop all**: Delete all tasks via `cron_list` + `cron_delete` for each

## Key Tools

| Tool | When to call |
|------|-------------|
| `cron_create` | Step 2 — register the task |
| `cron_list` | Step 4.2 — check if task still exists |
| `cron_mark_run` | Step 4.4 — after executing, get correct next `sleep_seconds` |
| `cron_delete` | Step 5 — stop a loop |

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  Agent (active agent via /agent)                   │
│                                                      │
│  1. cron_create → registers task, sleep_seconds: 52  │
│  2. bash async "sleep 52"                            │
│  3. (52 seconds pass)                                │
│  4. system_notification → agent wakes up           │
│  5. Agent acts on the prompt                       │
│  6. cron_mark_run → sleep_seconds: 60                │
│  7. bash async "sleep 60"                            │
│  8. (repeat from step 3)                             │
└──────────────────────────────────────────────────────┘
```

## Key Design Decisions

- **Registry-only cron server**: No background threads. The agent is the executor.
- **Async bash as timer**: Copilot CLI notifies the active agent when async bash completes.
- **`cron_mark_run`**: Tells the registry "I ran this" so it computes the correct next interval.
- **Session-scoped**: All tasks vanish when the session ends.
- **Agent-only**: Must be the active agent. Sub-agent delegation does not work for loops.
