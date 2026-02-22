#!/bin/zsh
# agent-presence: Agent presence tracking and heartbeat system

set -e

AGENT_PRESENCE_VERSION="1.0.0"
STATE_DIR="${AGENT_PRESENCE_STATE_DIR:-$HOME/_state/agents}"
PRESENCE_FILE="${STATE_DIR}/presence.tsv"
HEARTBEAT_PID_FILE="${STATE_DIR}/presence-heartbeat.pid"
MY_IDENTITY_FILE="${STATE_DIR}/.my_identity"

# Config
HEARTBEAT_INTERVAL="${AGENT_PRESENCE_HEARTBEAT_INTERVAL:-30}"
TIMEOUT_ONLINE=60
TIMEOUT_IDLE=300
TIMEOUT_AWAY=600

BUS_PATH="${AGENT_PRESENCE_BUS_PATH:-$HOME/founder_mode/_state/coordination/messages.tsv}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m'

# Ensure state directory exists
mkdir -p "$STATE_DIR"

# Initialize presence file if needed
if [ ! -f "$PRESENCE_FILE" ]; then
    echo -e "timestamp\tname\trole\tstatus\tcontext\tpid" > "$PRESENCE_FILE"
fi

log() {
    echo -e "${CYAN}[PRESENCE]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# ============================================
# IDENTITY MANAGEMENT
# ============================================
get_my_name() {
    if [ -f "$MY_IDENTITY_FILE" ]; then
        grep "^name=" "$MY_IDENTITY_FILE" | cut -d= -f2
    else
        echo "agent-$(whoami)"
    fi
}

get_my_role() {
    if [ -f "$MY_IDENTITY_FILE" ]; then
        grep "^role=" "$MY_IDENTITY_FILE" | cut -d= -f2
    fi
}

# ============================================
# BUS INTEGRATION
# ============================================
write_to_bus() {
    local msg_type="$1"
    local message="$2"
    local from_agent=$(get_my_name)
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    message=$(echo "$message" | tr '\t\n' ' ' | sed 's/  */ /g')
    printf "%s\t%s\tall\t%s\t%s\n" "$timestamp" "$from_agent" "$msg_type" "$message" >> "$BUS_PATH"
}

# ============================================
# PRESENCE OPERATIONS
# ============================================
cmd_register() {
    local name=""
    local role="operator"
    local context=""
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name) name="$2"; shift 2 ;;
            --role) role="$2"; shift 2 ;;
            --context) context="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    
    if [ -z "$name" ]; then
        name="$(whoami)-$(hostname | cut -d. -f1)"
    fi
    
    # Save identity
    echo "name=${name}" > "$MY_IDENTITY_FILE"
    echo "role=${role}" >> "$MY_IDENTITY_FILE"
    [ -n "$context" ] && echo "context=${context}" >> "$MY_IDENTITY_FILE"
    
    # Add to presence file
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local pid=$$
    
    # Remove old entry if exists
    grep -v "\t${name}\t" "$PRESENCE_FILE" > "${PRESENCE_FILE}.tmp" 2>/dev/null || true
    mv "${PRESENCE_FILE}.tmp" "$PRESENCE_FILE"
    
    # Add new entry
    printf "%s\t%s\t%s\tonline\t%s\t%s\n" "$timestamp" "$name" "$role" "$context" "$pid" >> "$PRESENCE_FILE"
    
    log "Registered as '$name' (role: $role)"
    write_to_bus "AGENT_REGISTER" "name=${name} role=${role} context=${context}"
}

cmd_deregister() {
    local name=$(get_my_name)
    
    if [ -f "$MY_IDENTITY_FILE" ]; then
        grep -v "\t${name}\t" "$PRESENCE_FILE" > "${PRESENCE_FILE}.tmp" 2>/dev/null || true
        mv "${PRESENCE_FILE}.tmp" "$PRESENCE_FILE"
        rm -f "$MY_IDENTITY_FILE"
        
        # Stop auto-heartbeat if running
        if [ -f "$HEARTBEAT_PID_FILE" ]; then
            local pid=$(cat "$HEARTBEAT_PID_FILE")
            kill "$pid" 2>/dev/null || true
            rm -f "$HEARTBEAT_PID_FILE"
        fi
        
        log "Deregistered '$name'"
        write_to_bus "AGENT_DEREGISTER" "name=${name}"
    else
        log "No identity to deregister"
    fi
}

cmd_heartbeat() {
    local auto=0
    local stop=0
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --auto) auto=1; shift ;;
            --stop) stop=1; shift ;;
            *) shift ;;
        esac
    done
    
    if [ $stop -eq 1 ]; then
        if [ -f "$HEARTBEAT_PID_FILE" ]; then
            local pid=$(cat "$HEARTBEAT_PID_FILE")
            kill "$pid" 2>/dev/null && log "Auto-heartbeat stopped"
            rm -f "$HEARTBEAT_PID_FILE"
        fi
        return
    fi
    
    if [ $auto -eq 1 ]; then
        # Start background heartbeat
        if [ -f "$HEARTBEAT_PID_FILE" ]; then
            local old_pid=$(cat "$HEARTBEAT_PID_FILE")
            kill "$old_pid" 2>/dev/null || true
        fi
        
        (
            while true; do
                cmd_heartbeat
                sleep "$HEARTBEAT_INTERVAL"
            done
        ) &
        
        echo $! > "$HEARTBEAT_PID_FILE"
        log "Auto-heartbeat started (PID: $!, interval: ${HEARTBEAT_INTERVAL}s)"
        return
    fi
    
    # Single heartbeat
    local name=$(get_my_name)
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local agent_status="online"
    
    # Update presence file
    if [ -f "$PRESENCE_FILE" ]; then
        local tmpfile="${PRESENCE_FILE}.tmp"
        while IFS=$'\t' read -r ts n r s c p; do
            if [ "$n" = "$name" ]; then
                printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$timestamp" "$n" "$r" "$agent_status" "$c" "$p" >> "$tmpfile"
            else
                printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$ts" "$n" "$r" "$s" "$c" "$p" >> "$tmpfile"
            fi
        done < "$PRESENCE_FILE"
        mv "$tmpfile" "$PRESENCE_FILE"
    fi
    
    # Write to bus occasionally (every 5th heartbeat to reduce noise)
    if [ $((RANDOM % 5)) -eq 0 ]; then
        write_to_bus "AGENT_HEARTBEAT" "name=${name} status=${status}"
    fi
}

cmd_list() {
    local now=$(date +%s)
    
    echo -e "${CYAN}=== ONLINE AGENTS ===${NC}"
    echo ""
    printf "${GRAY}%-20s %-12s %-10s %-8s${NC}\n" "NAME" "ROLE" "STATUS" "AGE"
    
    tail -n +2 "$PRESENCE_FILE" | sort -t$'\t' -k1 -r | awk -F'\t' '!seen[$2]++' | while IFS=$'\t' read -r ts name role agent_st context pid; do
        local ts_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" +%s 2>/dev/null || date -d "$ts" +%s 2>/dev/null || echo "0")
        local age=$((now - ts_epoch))
        local age_str
        
        if [ $age -lt 60 ]; then
            age_str="${age}s"
        elif [ $age -lt 3600 ]; then
            age_str="$((age / 60))m"
        else
            age_str="$((age / 3600))h"
        fi
        
        # Determine display status based on age
        local disp_status="$agent_st"
        local color="$GREEN"
        
        if [ $age -gt $TIMEOUT_AWAY ]; then
            disp_status="offline"
            color="$GRAY"
        elif [ $age -gt $TIMEOUT_IDLE ]; then
            disp_status="away"
            color="$RED"
        elif [ $age -gt $TIMEOUT_ONLINE ]; then
            disp_status="idle"
            color="$YELLOW"
        fi
        
        printf "${color}%-20s${NC} %-12s ${color}%-10s${NC} %-8s\n" "$name" "$role" "$disp_status" "$age_str"
    done
}

cmd_check() {
    local name=""
    local quiet=0
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --name) name="$2"; shift 2 ;;
            --quiet) quiet=1; shift ;;
            *) shift ;;
        esac
    done
    
    if [ -z "$name" ]; then
        name=$(get_my_name)
    fi
    
    local now=$(date +%s)
    local found=0
    local check_status=""
    local age=99999
    
    while IFS=$'\t' read -r ts n r s c p; do
        if [ "$n" = "$name" ]; then
            local ts_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$ts" +%s 2>/dev/null || date -d "$ts" +%s 2>/dev/null || echo "0")
            age=$((now - ts_epoch))
            check_status="$s"
            found=1
            break
        fi
    done < <(tail -n +2 "$PRESENCE_FILE")
    
    if [ $found -eq 0 ]; then
        [ $quiet -eq 0 ] && echo -e "${RED}Agent '$name' not found${NC}"
        return 1
    fi
    
    if [ $age -gt $TIMEOUT_AWAY ]; then
        [ $quiet -eq 0 ] && echo -e "${GRAY}$name: offline (last seen ${age}s ago)${NC}"
        return 1
    elif [ $age -gt $TIMEOUT_IDLE ]; then
        [ $quiet -eq 0 ] && echo -e "${RED}$name: away (idle ${age}s)${NC}"
        return 1
    elif [ $age -gt $TIMEOUT_ONLINE ]; then
        [ $quiet -eq 0 ] && echo -e "${YELLOW}$name: idle (${age}s)${NC}"
        return 0
    else
        [ $quiet -eq 0 ] && echo -e "${GREEN}$name: online (${age}s ago)${NC}"
        return 0
    fi
}

cmd_table() {
    cmd_list
}

cmd_dashboard() {
    while true; do
        clear
        echo -e "\033[1;42m AGENT PRESENCE DASHBOARD \033[0m $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        cmd_list
        echo ""
        echo -e "${GRAY}Press Ctrl+C to exit${NC}"
        sleep 5
    done
}

cmd_status() {
    log "agent-presence v${AGENT_PRESENCE_VERSION}"
    echo ""
    echo "Configuration:"
    echo "  STATE_DIR: $STATE_DIR"
    echo "  PRESENCE_FILE: $PRESENCE_FILE"
    echo "  HEARTBEAT_INTERVAL: ${HEARTBEAT_INTERVAL}s"
    echo "  TIMEOUTS: online=${TIMEOUT_ONLINE}s idle=${TIMEOUT_IDLE}s away=${TIMEOUT_AWAY}s"
    echo ""
    
    if [ -f "$MY_IDENTITY_FILE" ]; then
        echo "My Identity:"
        cat "$MY_IDENTITY_FILE" | sed 's/^/  /'
    else
        echo "Not registered"
    fi
    echo ""
    
    cmd_list
}

# ============================================
# MAIN
# ============================================
case "${1:-status}" in
    register)
        shift
        cmd_register "$@"
        ;;
    deregister|unregister)
        cmd_deregister
        ;;
    heartbeat)
        shift
        cmd_heartbeat "$@"
        ;;
    list|ls)
        cmd_list
        ;;
    check)
        shift
        cmd_check "$@"
        ;;
    table)
        cmd_table
        ;;
    dashboard)
        cmd_dashboard
        ;;
    status|info)
        cmd_status
        ;;
    help|--help|-h)
        cat << 'EOF'
agent-presence: Agent presence tracking and heartbeat

Usage: agent-presence [command]

Commands:
  register [--name X] [--role Y] [--context Z]  Register agent
  deregister                                    Remove agent from presence
  heartbeat [--auto] [--stop]                   Send heartbeat
  list                                          List all online agents
  check [--name X] [--quiet]                    Check specific agent status
  table                                         Show status table
  dashboard                                     Real-time dashboard
  status                                        Show system status
  help                                          Show this help

Examples:
  agent-presence register --name "claude-code" --role "advisor"
  agent-presence heartbeat --auto &
  agent-presence check --name "codex-vscode" --quiet && echo "Online!"
EOF
        ;;
    *)
        error "Unknown command: $1"
        echo "Use 'agent-presence help' for usage"
        exit 1
        ;;
esac
