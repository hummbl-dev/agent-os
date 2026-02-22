---
name: workflow-runner
description: DAG-based workflow execution engine for coordinating multi-step tasks across terminal sessions and agents. Supports dependency chains, parallel execution, checkpoint/resume, and integration with coordination bus.
metadata:
  {
    "openclaw":
      {
        "emoji": "🔄",
        "requires": { "bins": ["bash", "date", "mkdir", "pgrep"] },
        "install": [],
      },
  }
---

# workflow-runner

Execute complex workflows as directed acyclic graphs (DAGs) across terminal sessions and agents. Supports dependencies, parallel execution, checkpoint/resume, and full integration with the coordination bus.

## Quick Start

```bash
# Run a workflow from YAML definition
workflow-runner run ./my-workflow.yaml

# Check workflow status
workflow-runner status --id workflow-20240213-001

# List active workflows
workflow-runner list

# Resume from checkpoint
workflow-runner resume --id workflow-20240213-001
```

## Core Capabilities

### 1. Workflow Definition

Define workflows as YAML DAGs:

```yaml
# example-workflow.yaml
name: morning-routine
version: "1.0"

tasks:
  - id: check-email
    command: "echo 'Checking email...'"
    session: ttys001
    
  - id: generate-briefing
    command: "python -m founder_mode.services.briefing"
    depends_on: [check-email]
    session: ttys002
    timeout: 120
    
  - id: send-signal
    command: "curl -X POST http://localhost:8080/v1/messages"
    depends_on: [generate-briefing]
    session: ttys003
    retries: 3
    
  - id: update-calendar
    command: "python -m founder_mode.integrations.google_calendar"
    # No depends_on - runs in parallel with check-email
    session: ttys004
```

### 2. Execution Commands

```bash
# Run workflow
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh run workflow.yaml

# Run with custom ID
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh run workflow.yaml --id my-run-001

# Dry run (validate without executing)
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh run workflow.yaml --dry-run

# Run specific task only
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh run workflow.yaml --task check-email
```

### 3. Monitoring & Control

```bash
# List all workflows
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh list

# Show workflow status
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh status --id my-run-001

# Show detailed task status
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh tasks --id my-run-001

# Pause workflow
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh pause --id my-run-001

# Resume workflow
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh resume --id my-run-001

# Cancel workflow
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh cancel --id my-run-001
```

### 4. Checkpoint & Resume

Workflows automatically checkpoint after each task:

```bash
# Resume from last checkpoint
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh resume --id my-run-001

# Resume from specific task
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh resume --id my-run-001 --from-task generate-briefing

# Force restart (ignore checkpoint)
~/agent-unified/skills/workflow-runner/scripts/workflow-runner.sh run workflow.yaml --id my-run-001 --force
```

## Workflow Schema

### Task Properties

| Property | Required | Description |
|----------|----------|-------------|
| `id` | Yes | Unique task identifier |
| `command` | Yes | Shell command to execute |
| `depends_on` | No | List of task IDs that must complete first |
| `session` | No | Target TTY/tmux session (default: current) |
| `timeout` | No | Timeout in seconds (default: 300) |
| `retries` | No | Retry attempts on failure (default: 0) |
| `env` | No | Environment variables dictionary |
| `on_success` | No | Next task ID on success |
| `on_failure` | No | Next task ID on failure |

### Session Targeting

```yaml
# Target specific TTY
session: ttys001

# Target tmux session/window
session: tmux:my-session:0

# Target by process pattern
session: pgrep:claude

# Current session (default)
session: current
```

## Integration with Coordination Bus

Workflow events are published to the coordination bus:

```
# Workflow started
timestamp	runner	all	WORKFLOW_START	id=my-run-001 tasks=4

# Task started
timestamp	runner	all	TASK_START	workflow=my-run-001 task=check-email

# Task completed
timestamp	runner	all	TASK_COMPLETE	workflow=my-run-001 task=check-email duration=5s

# Task failed
timestamp	runner	all	TASK_FAILED	workflow=my-run-001 task=send-signal error=timeout

# Workflow completed
timestamp	runner	all	WORKFLOW_COMPLETE	id=my-run-001 status=success duration=120s
```

## State Management

Workflow state is stored in:

```
~/agent-unified/skills/workflow-runner/state/
├── workflows.tsv          # Workflow registry
├── my-run-001/
│   ├── checkpoint.json    # Last checkpoint
│   ├── tasks/
│   │   ├── task-001.log
│   │   └── task-002.log
│   └── status.json
```

## Templates

Quick-start templates included:

```bash
# Morning briefing workflow
workflow-runner template morning-briefing > morning.yaml

# Multi-agent coordination
workflow-runner template multi-agent > agents.yaml

# Backup & maintenance
workflow-runner template maintenance > backup.yaml
```

## Configuration

Environment variables:

```bash
export WORKFLOW_STATE_DIR="$HOME/agent-unified/skills/workflow-runner/state"
export WORKFLOW_BUS_PATH="$HOME/founder_mode/_state/coordination/messages.tsv"
export WORKFLOW_DEFAULT_TIMEOUT=300
export WORKFLOW_MAX_PARALLEL=4
```

## Safety Features

- **Dry run mode**: Validate workflow without executing
- **Timeout protection**: All tasks have configurable timeouts
- **Resource limits**: Max parallel execution configurable
- **Checkpoint on failure**: Resume from last known good state
- **Signal handling**: Graceful shutdown on SIGINT/SIGTERM
- **Session validation**: Verify target sessions exist before execution
