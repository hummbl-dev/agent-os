---
name: recon-bridge
description: Bridge between terminal reconnaissance system (.recon/) and the agent coordination bus. Publishes terminal state, session changes, and process intelligence to the shared message bus.
metadata:
  {
    "openclaw":
      {
        "emoji": "🔍",
        "requires": { "bins": ["who", "ps", "pgrep", "tmux", "lsof"] },
        "install": ["~/.recon/reconrc"],
      },
  }
---

# recon-bridge

Connects the terminal reconnaissance system to the agent coordination bus, enabling agents to see and react to terminal state changes.

## Quick Start

```bash
# Publish current terminal state to coordination bus
recon-bridge publish

# Start continuous monitoring (background)
recon-bridge monitor start

# Stop monitoring
recon-bridge monitor stop

# Check bridge status
recon-bridge status
```

## Core Capabilities

### 1. Terminal State Publishing

Capture and publish terminal session information:

```bash
# Publish snapshot immediately
~/agent-unified/skills/recon-bridge/scripts/recon-bridge.sh publish

# Publish with custom message type
~/agent-unified/skills/recon-bridge/scripts/recon-bridge.sh publish --type STATUS
```

### 2. Session Change Detection

Detect and announce new/closed terminal sessions:

```bash
# Check for session changes since last poll
~/agent-unified/skills/recon-bridge/scripts/recon-bridge.sh detect

# Auto-announce changes to bus
~/agent-unified/skills/recon-bridge/scripts/recon-bridge.sh detect --announce
```

### 3. Process Intelligence

Track agent processes and resource usage:

```bash
# Publish process snapshot
~/agent-unified/skills/recon-bridge/scripts/recon-bridge.sh processes

# Track specific agent processes
~/agent-unified/skills/recon-bridge/scripts/recon-bridge.sh processes --agent kimic
```

### 4. Continuous Monitoring

Background monitoring with periodic snapshots:

```bash
# Start monitor (30s interval)
~/agent-unified/skills/recon-bridge/scripts/recon-bridge.sh monitor start

# Custom interval (60 seconds)
~/agent-unified/skills/recon-bridge/scripts/recon-bridge.sh monitor start --interval 60

# Stop monitor
~/agent-unified/skills/recon-bridge/scripts/recon-bridge.sh monitor stop

# Check monitor status
~/agent-unified/skills/recon-bridge/scripts/recon-bridge.sh monitor status
```

## Message Format

Published messages use these types on the coordination bus:

| Type | Description | Payload |
|------|-------------|---------|
| `RECON_SNAPSHOT` | Full terminal state | sessions, processes, tmux info |
| `SESSION_START` | New terminal session | tty, user, timestamp |
| `SESSION_END` | Terminal closed | tty, duration |
| `AGENT_PROCESS` | Agent process detected | pid, agent_type, cmd |
| `RESOURCE_ALERT` | Resource threshold crossed | metric, value, threshold |

## Integration with Lead Doctor

Lead Doctor automatically subscribes to recon-bridge messages:

```bash
# In Lead Doctor dashboard, recon data appears as:
# [RECON] 3 active sessions | 2 agents online | CPU: 12%
```

## Configuration

Environment variables (set in `~/.recon/reconrc`):

```bash
export RECON_BRIDGE_ENABLED=1          # Enable bridge
export RECON_BRIDGE_INTERVAL=30        # Poll interval (seconds)
export RECON_BRIDGE_BUS_PATH="$HOME/founder_mode/_state/coordination/messages.tsv"
```

## Safety Notes

- Bridge only publishes data from own user's sessions
- No sensitive command content is captured (only metadata)
- Process lists are filtered to relevant agents only
- All writes are append-only to coordination bus
