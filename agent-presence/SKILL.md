---
name: agent-presence
description: Agent presence detection and heartbeat system. Tracks which agents are online, their activity status, and provides real-time availability awareness across the agent fleet.
metadata:
  {
    "openclaw":
      {
        "emoji": "🟢",
        "requires": { "bins": ["date", "ps", "pgrep"] },
        "install": [],
      },
  }
---

# agent-presence

Real-time agent presence tracking with heartbeat protocol. Enables agents to discover who's online, check availability, and route messages intelligently.

## Quick Start

```bash
# Register your presence as an agent
agent-presence register --name "claude-code" --role "advisor"

# Send heartbeat (do this every 30s while active)
agent-presence heartbeat

# Check who's online
agent-presence status

# Show presence dashboard
agent-presence dashboard
```

## Core Capabilities

### 1. Registration

Register an agent when it starts:

```bash
# Basic registration
~/agent-unified/skills/agent-presence/scripts/agent-presence.sh register --name "kimi"

# With role and metadata
~/agent-unified/skills/agent-presence/scripts/agent-presence.sh register \
    --name "codex-vscode" \
    --role "executor" \
    --context "founder_mode/integrations"
```

### 2. Heartbeat

Maintain presence with periodic heartbeats:

```bash
# Send single heartbeat
~/agent-unified/skills/agent-presence/scripts/agent-presence.sh heartbeat

# Start auto-heartbeat (background, 30s interval)
~/agent-unified/skills/agent-presence/scripts/agent-presence.sh heartbeat --auto

# Stop auto-heartbeat
~/agent-unified/skills/agent-presence/scripts/agent-presence.sh heartbeat --stop
```

### 3. Presence Queries

Check who's online and their status:

```bash
# List all online agents
~/agent-unified/skills/agent-presence/scripts/agent-presence.sh list

# Check specific agent
~/agent-unified/skills/agent-presence/scripts/agent-presence.sh check --name "claude-code"

# Show detailed status
~/agent-unified/skills/agent-presence/scripts/agent-presence.sh status
```

### 4. Availability Dashboard

Real-time view of agent fleet:

```bash
# Show dashboard (auto-refresh)
~/agent-unified/skills/agent-presence/scripts/agent-presence.sh dashboard

# One-shot status table
~/agent-unified/skills/agent-presence/scripts/agent-presence.sh table
```

## Agent Status States

| State | Description | Timeout |
|-------|-------------|---------|
| `online` | Active and responsive | 60s |
| `idle` | No recent activity | 5 min |
| `away` | Heartbeat stale | 10 min |
| `offline` | No heartbeat | > 10 min |

## Integration with Coordination Bus

Presence events are published to the coordination bus:

```
# Registration
timestamp	agent-name	all	AGENT_REGISTER	name=claude-code role=advisor

# Heartbeat
timestamp	agent-name	all	AGENT_HEARTBEAT	status=online activity=coding

# Status change
timestamp	agent-name	all	AGENT_STATUS	old=online new=idle
```

## Configuration

Environment variables:

```bash
export AGENT_PRESENCE_ENABLED=1           # Enable presence system
export AGENT_PRESENCE_HEARTBEAT_INTERVAL=30  # Seconds between heartbeats
export AGENT_PRESENCE_TIMEOUT=600         # Mark offline after (seconds)
export AGENT_PRESENCE_STATE_DIR="$HOME/_state/agents"
```

## Shell Integration

Add to agent startup script:

```bash
# In ~/.zshrc or agent entry script
source ~/agent-unified/skills/agent-presence/scripts/agent-presence.sh

# On agent start
agent-presence register --name "$(whoami)-$(hostname)" --role "operator"

# Start heartbeat
agent-presence heartbeat --auto &

# On exit, deregister
trap 'agent-presence deregister' EXIT
```

## Programmatic Usage

```bash
# Check if agent is online before sending message
if agent-presence check --name "codex-vscode" --quiet; then
    echo "Codex is online, sending message..."
    # ... send to coordination bus
else
    echo "Codex is offline, queuing for later..."
fi
```

## Safety Notes

- Presence data is local-only (no network exposure)
- Heartbeats are lightweight (just timestamp + name)
- Stale agents auto-expire after timeout
- Graceful shutdown should deregister
