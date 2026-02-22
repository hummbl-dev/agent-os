#!/bin/zsh
# recon-bridge: Bridge between .recon/ and coordination bus
# Publishes terminal state to agent coordination bus

set -e

RECON_BRIDGE_VERSION="1.0.0"
RECON_DIR="${RECON_DIR:-$HOME/.recon}"
STATE_DIR="${RECON_DIR}/state"
BUS_PATH="${RECON_BRIDGE_BUS_PATH:-$HOME/founder_mode/_state/coordination/messages.tsv}"
PID_FILE="${STATE_DIR}/recon-bridge.pid"
LAST_STATE_FILE="${STATE_DIR}/recon-bridge.last"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Ensure directories exist
mkdir -p "$STATE_DIR"

log() {
    echo -e "${CYAN}[RECON-BRIDGE]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# ============================================
# BUS WRITE UTILITY
# ============================================
write_to_bus() {
    local msg_type="$1"
    local message="$2"
    local from_agent="${3:-recon-bridge}"
    local to_agent="${4:-all}"
    
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Sanitize message (remove tabs/newlines)
    message=$(echo "$message" | tr '\t\n' ' ' | sed 's/  */ /g')
    
    # Append to bus
    printf "%s\t%s\t%s\t%s\t%s\n" "$timestamp" "$from_agent" "$to_agent" "$msg_type" "$message" >> "$BUS_PATH"
}

# ============================================
# RECON DATA GATHERING
# ============================================
gather_sessions() {
    # Get active sessions
    local sessions=""
    while IFS= read -r line; do
        local tty=$(echo "$line" | awk '{print $2}')
        local user=$(echo "$line" | awk '{print $1}')
        if [ -n "$tty" ]; then
            local proc_count=$(ps -t "$tty" 2>/dev/null | wc -l)
            sessions="${sessions}${tty}(${proc_count}),"
        fi
    done < <(who | awk '{print $1, $2}')
    echo "${sessions%,}"
}

gather_tmux() {
    if ! command -v tmux &>/dev/null; then
        echo "tmux-not-installed"
        return
    fi
    
    if ! tmux list-sessions &>/dev/null; then
        echo "no-sessions"
        return
    fi
    
    tmux list-sessions -F "#{session_name}(#{session_windows}w,#{?session_attached,attached,detached})" 2>/dev/null | tr '\n' ',' | sed 's/,$//'
}

gather_agent_processes() {
    local agents=""
    local pids=$(pgrep -f "(claude|codex|kimi)" | grep -v grep | tr '\n' ' ')
    
    for pid in $pids; do
        if [ -n "$pid" ]; then
            local cmd=$(ps -o comm= -p "$pid" 2>/dev/null | tr -d ' ')
            local cpu=$(ps -o pcpu= -p "$pid" 2>/dev/null | tr -d ' ')
            local mem=$(ps -o rss= -p "$pid" 2>/dev/null | awk '{print int($1/1024)"MB"}')
            agents="${agents}${pid}:${cmd}:${cpu}:${mem},"
        fi
    done
    echo "${agents%,}"
}

gather_resource_summary() {
    local cpu=$(ps aux | awk 'NR>1 {sum+=$3} END {printf "%.1f", sum}')
    local mem=$(vm_stat | grep "Pages active" | awk '{print $3}' | sed 's/\.//' | awk '{printf "%.0f", $1*4096/1024/1024}')
    echo "CPU:${cpu},MEM:${mem}MB"
}

# ============================================
# COMMANDS
# ============================================
cmd_publish() {
    local msg_type="${1:-RECON_SNAPSHOT}"
    
    log "Gathering terminal state..."
    
    local sessions=$(gather_sessions)
    local tmux=$(gather_tmux)
    local agents=$(gather_agent_processes)
    local resources=$(gather_resource_summary)
    
    local payload="sessions=[${sessions}] tmux=[${tmux}] agents=[${agents}] resources=[${resources}]"
    
    write_to_bus "$msg_type" "$payload"
    log "Published ${msg_type} to coordination bus"
    echo "  Sessions: $sessions"
    echo "  Tmux: $tmux"
    echo "  Agents: $agents"
    echo "  Resources: $resources"
}

cmd_detect() {
    local announce=0
    [[ "$1" == "--announce" ]] && announce=1
    
    local current_sessions=$(gather_sessions)
    
    if [ -f "$LAST_STATE_FILE" ]; then
        local last_sessions=$(cat "$LAST_STATE_FILE")
        
        if [ "$current_sessions" != "$last_sessions" ]; then
            log "Session change detected!"
            
            if [ $announce -eq 1 ]; then
                local added=$(echo "$current_sessions" | tr ',' '\n' | grep -vFxf <(echo "$last_sessions" | tr ',' '\n') | tr '\n' ',' | sed 's/,$//')
                local removed=$(echo "$last_sessions" | tr ',' '\n' | grep -vFxf <(echo "$current_sessions" | tr ',' '\n') | tr '\n' ',' | sed 's/,$//')
                
                [ -n "$added" ] && write_to_bus "SESSION_START" "new_sessions=${added}"
                [ -n "$removed" ] && write_to_bus "SESSION_END" "closed_sessions=${removed}"
                
                log "Announced changes to bus"
            fi
        else
            log "No session changes"
        fi
    fi
    
    echo "$current_sessions" > "$LAST_STATE_FILE"
}

cmd_processes() {
    local filter_agent=""
    [[ "$1" == "--agent" ]] && filter_agent="$2"
    
    local agents=$(gather_agent_processes)
    
    if [ -n "$filter_agent" ]; then
        agents=$(echo "$agents" | tr ',' '\n' | grep -i "$filter_agent" | tr '\n' ',' | sed 's/,$//')
    fi
    
    write_to_bus "AGENT_PROCESS" "processes=[${agents}]"
    log "Published agent processes"
    echo "  $agents"
}

cmd_monitor_start() {
    local interval=30
    [[ "$1" == "--interval" ]] && interval="$2"
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "Monitor already running (PID: $pid)"
            return 1
        fi
    fi
    
    log "Starting recon-bridge monitor (interval: ${interval}s)..."
    
    (
        while true; do
            cmd_publish "RECON_SNAPSHOT" >/dev/null 2>&1
            cmd_detect --announce >/dev/null 2>&1
            sleep "$interval"
        done
    ) &
    
    echo $! > "$PID_FILE"
    log "Monitor started (PID: $!)"
    write_to_bus "SYSTEM" "recon-bridge monitor started (interval=${interval}s)"
}

cmd_monitor_stop() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill "$pid" 2>/dev/null; then
            log "Monitor stopped (PID: $pid)"
            write_to_bus "SYSTEM" "recon-bridge monitor stopped"
        fi
        rm -f "$PID_FILE"
    else
        log "No monitor running"
    fi
}

cmd_monitor_status() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}Monitor running${NC} (PID: $pid)"
            local uptime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
            echo "  Uptime: $uptime"
        else
            echo -e "${YELLOW}Monitor PID file exists but process not running${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${RED}Monitor not running${NC}"
    fi
}

cmd_status() {
    log "recon-bridge v${RECON_BRIDGE_VERSION}"
    echo ""
    cmd_monitor_status
    echo ""
    echo "Configuration:"
    echo "  BUS_PATH: $BUS_PATH"
    echo "  STATE_DIR: $STATE_DIR"
    echo "  PID_FILE: $PID_FILE"
    echo ""
    echo "Current state:"
    echo "  Sessions: $(gather_sessions)"
    echo "  Tmux: $(gather_tmux)"
    echo "  Agents: $(gather_agent_processes)"
}

# ============================================
# MAIN
# ============================================
case "${1:-status}" in
    publish)
        cmd_publish "$2"
        ;;
    detect)
        cmd_detect "$2"
        ;;
    processes)
        cmd_processes "$2" "$3"
        ;;
    monitor)
        case "${2:-status}" in
            start) cmd_monitor_start "$3" "$4" ;;
            stop) cmd_monitor_stop ;;
            status) cmd_monitor_status ;;
            *) echo "Usage: recon-bridge monitor [start|stop|status]" ;;
        esac
        ;;
    status|info)
        cmd_status
        ;;
    help|--help|-h)
        cat << 'EOF'
recon-bridge: Bridge terminal recon to coordination bus

Usage: recon-bridge [command]

Commands:
  publish [type]          Publish snapshot to bus (default: RECON_SNAPSHOT)
  detect [--announce]     Detect session changes, optionally announce
  processes [--agent X]   Publish agent process list
  monitor start [--interval N]  Start background monitoring
  monitor stop            Stop background monitoring  
  monitor status          Check monitor status
  status                  Show bridge status and config
  help                    Show this help

Examples:
  recon-bridge publish                    # Quick snapshot
  recon-bridge detect --announce          # Detect and announce changes
  recon-bridge monitor start --interval 60  # Start with 60s interval
  recon-bridge processes --agent claude   # Track claude processes
EOF
        ;;
    *)
        error "Unknown command: $1"
        echo "Use 'recon-bridge help' for usage"
        exit 1
        ;;
esac
