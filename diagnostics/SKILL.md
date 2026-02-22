---
name: diagnostics
description: System diagnostics, health monitoring, and recovery coordination for agent fleets and infrastructure.
metadata:
  {
    "openclaw":
      {
        "emoji": "🩺",
        "requires": { "bins": ["ps", "lsof", "netstat", "curl", "df", "du", "vm_stat", "iostat"] },
        "install": [],
      },
  }
---

# diagnostics

System diagnostics and health monitoring skill for agent fleets, services, and infrastructure. Provides systematic troubleshooting, health assessment, and recovery coordination.

## Core Capabilities

### 1. Process Diagnostics

Check running processes and agent states:

```bash
# List all agent processes
ps aux | grep -E "(claude|codex|kimi)" | grep -v grep

# Check working directories of agents
lsof -u $(whoami) | grep -E "(kimi|claude|codex)" | grep cwd

# Check TTY assignments
ps -o pid,tty,comm,args -u $(whoami) | grep -E "ttys"

# Get detailed process stats (CPU, memory, time)
ps -o pid,ppid,pcpu,pmem,etime,comm,args -p <PID>
```

### 2. Resource Diagnostics

#### Memory Analysis

```bash
# System memory overview
vm_stat | head -10

# Memory pressure
memory_pressure

# Top memory consumers
ps aux | sort -rk 4 | head -10

# Agent-specific memory usage
for pid in $(pgrep -f "(claude|codex|kimi)"); do
    echo "PID $pid: $(ps -o rss= -p $pid | awk '{print $1/1024 " MB"}')"
done
```

#### Disk Usage

```bash
# Overall disk space
df -h /
df -h /Users

# Large files in state directory
find _state -type f -size +10M -exec ls -lh {} \;

# Directory sizes
du -sh _state/coordination/
du -sh agents/*/memory/ 2>/dev/null

# Log file sizes
ls -lh _state/coordination/*.log 2>/dev/null
ls -lh _state/*.log 2>/dev/null
```

#### CPU Load

```bash
# Load average
uptime

# Per-process CPU over time
iostat -c 3

# CPU-intensive processes
ps aux | sort -rk 3 | head -10
```

### 3. Network Diagnostics

```bash
# Check network connectivity
ping -c 3 8.8.8.8

# DNS resolution
dig +short google.com

# Open connections for agents
lsof -i | grep -E "(claude|codex|kimi)"

# Check if coordination bus is accessible
ls -la _state/coordination/messages.tsv

# Network interface status
ifconfig | grep -E "(en0|en1|status)" | head -10
```

### 4. Response Time Checks

```bash
# File system response (coordination bus write)
time echo "test" >> _state/coordination/messages.tsv && tail -1 _state/coordination/messages.tsv

# Git status response time
cd /Users/others && time git status --short > /dev/null

# Process spawn time
time ps aux > /dev/null

# Log append latency
start=$(date +%s%N)
echo "test" >> _state/coordination/claire.log
end=$(date +%s%N)
echo "Log write latency: $(( (end - start) / 1000000 )) ms"
```

### 5. Coordination Bus Health

Monitor the message bus and state files:

```bash
# Check message bus activity
tail -20 _state/coordination/messages.tsv

# Message velocity (messages per hour)
awk -F'\t' -v date=$(date -v-1H +"%Y-%m-%dT%H") '$1 > date {count++} END {print count " messages in last hour"}' _state/coordination/messages.tsv

# Check heartbeat status
tail -20 _state/coordination/heartbeat.tsv

# Check gate status
tail -10 _state/coordination/gate-status.tsv

# Count events by type
awk -F'\t' '{print $4}' _state/coordination/messages.tsv | sort | uniq -c | sort -rn | head -10

# Detect anomalies (errors, blocks, failures)
grep -iE "(error|fail|blocked|crash)" _state/coordination/messages.tsv | tail -10
```

### 6. Log Health Analysis

```bash
# Check Claire monitor log
tail -30 _state/coordination/claire.log

# Error rate in logs
grep -c "ERROR" _state/coordination/claire.log
grep -c "FAIL" _state/coordination/gate-status.tsv

# Log rotation needs (files > 100MB)
find _state -name "*.log" -size +100M

# Recent tool activity
tail -20 _state/coordination/tool-activity.tsv

# Scheduler logs
tail -10 _state/briefing_scheduler.out.log
tail -10 _state/briefing_scheduler.err.log

# Check for error patterns in last hour
grep "$(date -v-1H +"%Y-%m-%dT%H")" _state/coordination/claire.log | grep -iE "(error|warn)" | tail -10
```

### 7. Agent State Assessment

Evaluate individual agent health:

```bash
# List all agent directories
ls -la agents/ | grep -v "^total"

# Check agent memory files
ls -la agents/<name>/memory/

# Review recent agent actions
cat agents/<name>/actions/* 2>/dev/null | tail -20

# Check agent report timestamps
find agents -name "*.md" -path "*/reports/*" -mtime -1

# Agent file counts (bloat detection)
for agent in agents/*/; do
    count=$(find "$agent" -type f 2>/dev/null | wc -l)
    size=$(du -sh "$agent" 2>/dev/null | cut -f1)
    echo "$(basename $agent): $count files, $size"
done
```

### 8. File System Health

```bash
# Check for permission issues
find _state ! -writable -type f 2>/dev/null

# Inode usage
df -i /

# Fragmentation (macOS)
fsck -n / 2>/dev/null || echo "FS check requires single user mode"

# Symlink health
find . -type l ! -exec test -e {} \; -print 2>/dev/null | head -10
```

## Diagnostic Patterns

### Stale Heartbeat Detection

```bash
# Check if heartbeat is stale (older than 1 hour)
last_beat=$(tail -1 _state/coordination/heartbeat.tsv | cut -f1)
last_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$last_beat" +%s 2>/dev/null || date -d "$last_beat" +%s)
now=$(date +%s)
diff=$(( (now - last_epoch) / 60 ))
echo "Last heartbeat: $diff minutes ago"
[ $diff -gt 30 ] && echo "⚠️ STALE HEARTBEAT"
```

### Memory Leak Detection

```bash
# Track agent memory over time
for i in 1 2 3; do
    ps aux | grep -E "(claude|codex|kimi)" | grep -v grep | awk '{print $5, $11}'
    sleep 5
done
```

### Blocked Agent Detection

```bash
# Find BLOCKED agents in messages with context
grep "BLOCKED" _state/coordination/messages.tsv | tail -5

# Check if blocked agent is still active
blocked_agent=$(grep "BLOCKED" _state/coordination/messages.tsv | tail -1 | cut -f2)
ps aux | grep "$blocked_agent" | grep -v grep
```

### Orphaned Process Detection

```bash
# Find agent processes without valid TTY
ps aux | grep -E "(claude|codex|kimi)" | grep -v grep | awk '{if ($7 == "??") print $0}'

# Find zombie processes
ps aux | awk '$8 == "Z" {print $0}'
```

### Disk Space Critical Detection

```bash
# Check if disk is nearly full
df -h / | awk 'NR==2 {gsub(/%/,""); if ($5 > 90) print "⚠️ DISK CRITICAL: " $5 "% used"}'
```

## Recovery Actions

### Graceful Agent Restart

1. Identify agent PID: `ps aux | grep <agent-name>`
2. Check active tasks in coordination bus
3. Notify other agents via messages.tsv
4. Terminate: `kill -TERM <pid>`
5. Wait 5 seconds, verify shutdown
6. Restart if needed

### Coordination Bus Recovery

1. Archive current messages: `cp messages.tsv messages.archive.$(date +%s).tsv`
2. Trim to last 100 lines: `tail -100 messages.tsv > messages.tmp && mv messages.tmp messages.tsv`
3. Verify write permissions
4. Emit SYSTEM_RESTARTED event

### State File Cleanup

```bash
# Archive old state files
cd _state/coordination/
mv tool-activity.tsv archive/tool-activity.$(date +%Y%m%d).tsv
# Reset with headers
```

### Log Rotation

```bash
# Manual log rotation
for log in _state/coordination/*.log; do
    if [ $(stat -f%z "$log" 2>/dev/null || stat -c%s "$log" 2>/dev/null) -gt 104857600 ]; then
        mv "$log" "$log.$(date +%Y%m%d)"
        touch "$log"
        echo "Rotated: $log"
    fi
done
```

## Health Metrics

| Metric | Normal Range | Alert Threshold | Critical |
|--------|--------------|-----------------|----------|
| messages.tsv size | < 10MB | > 50MB | > 100MB |
| heartbeat age | < 5 min | > 30 min | > 2 hours |
| Active agents | 3-8 | < 2 or > 15 | < 1 or > 20 |
| Gate failures | 0 | > 5/hour | > 10/hour |
| Tool errors | < 5% | > 20% | > 50% |
| Disk usage | < 70% | > 85% | > 95% |
| Memory pressure | < 50% | > 75% | > 90% |
| CPU load | < 2.0 | > 5.0 | > 10.0 |
| Log write latency | < 100ms | > 500ms | > 2000ms |
| Agent memory | < 500MB | > 1GB | > 2GB |

## Advanced Diagnostics

### System Call Tracing (macOS)

```bash
# Trace file operations by an agent
sudo dtruss -p <PID> 2>&1 | grep -E "(open|write|close)"
```

### Network Packet Capture

```bash
# Capture coordination bus traffic (if networked)
sudo tcpdump -i lo0 -A | grep -E "(AGENT|HEARTBEAT|BLOCKED)"
```

### Performance Profiling

```bash
# Sample process activity
sudo sample <PID> 5 -file /tmp/agent_sample.txt
```

## Integration with Lead Doctor

- Lead Doctor uses this skill for systematic diagnostics
- Automated health checks emit to coordination bus
- Recovery actions are logged and tracked
- Escalation to human when auto-recovery fails
- Historical trends stored in `agents/lead-doctor/reports/`

## Safety Notes

- Always check active tasks before terminating agents
- Archive before deleting state files
- Verify rollback plans exist for destructive actions
- Respect Warden gates for recovery operations
- Never use `kill -9` without attempting graceful shutdown first
