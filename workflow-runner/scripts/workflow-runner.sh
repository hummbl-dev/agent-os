#!/bin/zsh
# workflow-runner: DAG-based workflow execution engine

set -e

WORKFLOW_VERSION="1.0.0"
SKILL_DIR="${WORKFLOW_SKILL_DIR:-$HOME/agent-unified/skills/workflow-runner}"
STATE_DIR="${WORKFLOW_STATE_DIR:-$SKILL_DIR/state}"
BUS_PATH="${WORKFLOW_BUS_PATH:-$HOME/founder_mode/_state/coordination/messages.tsv}"
DEFAULT_TIMEOUT="${WORKFLOW_DEFAULT_TIMEOUT:-300}"
MAX_PARALLEL="${WORKFLOW_MAX_PARALLEL:-4}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m'

# Ensure directories exist
mkdir -p "$STATE_DIR"

log() {
    echo -e "${CYAN}[WORKFLOW]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# ============================================
# BUS INTEGRATION
# ============================================
write_to_bus() {
    local msg_type="$1"
    local message="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    message=$(echo "$message" | tr '\t\n' ' ' | sed 's/  */ /g')
    printf "%s\tworkflow-runner\tall\t%s\t%s\n" "$timestamp" "$msg_type" "$message" >> "$BUS_PATH"
}

# ============================================
# WORKFLOW STATE MANAGEMENT
# ============================================
generate_workflow_id() {
    local prefix="${1:-wf}"
    echo "${prefix}-$(date +%Y%m%d-%H%M%S)-$$"
}

init_workflow_state() {
    local workflow_id="$1"
    local workflow_file="$2"
    
    local workflow_dir="$STATE_DIR/$workflow_id"
    mkdir -p "$workflow_dir/tasks"
    
    echo "{\"id\": \"$workflow_id\", \"file\": \"$workflow_file\", \"status\": \"initialized\", \"started\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$workflow_dir/status.json"
    
    echo "$workflow_id"
}

update_workflow_status() {
    local workflow_id="$1"
    local status="$2"
    local meta="${3:-}"
    
    local workflow_dir="$STATE_DIR/$workflow_id"
    local status_file="$workflow_dir/status.json"
    
    if [ -f "$status_file" ]; then
        local current=$(cat "$status_file")
        local updated=$(echo "$current" | sed "s/\"status\": \"[^\"]*\"/\"status\": \"$status\"/")
        [ -n "$meta" ] && updated=$(echo "$updated" | sed "s/}$/, $meta}/")
        echo "$updated" > "$status_file"
    fi
}

# ============================================
# WORKFLOW PARSING
# ============================================
parse_workflow() {
    local workflow_file="$1"
    
    if [ ! -f "$workflow_file" ]; then
        error "Workflow file not found: $workflow_file"
        return 1
    fi
    
    # Basic YAML parsing - extract tasks
    # This is a simplified parser; real implementation would use yq or similar
    local in_tasks=0
    local current_task=""
    local task_count=0
    
    while IFS= read -r line; do
        # Detect tasks section
        if [[ "$line" =~ ^tasks: ]]; then
            in_tasks=1
            continue
        fi
        
        # Detect new task (2-space indent + - id:)
        if [[ $in_tasks -eq 1 && "$line" =~ ^[[:space:]]*-[[:space:]]*id:[[:space:]]*(.+) ]]; then
            [ -n "$current_task" ] && echo "$current_task"
            current_task="id:${match[1]}"
            task_count=$((task_count + 1))
        elif [[ $in_tasks -eq 1 && -n "$current_task" && "$line" =~ ^[[:space:]]+([a-z_]+):[[:space:]]*(.*) ]]; then
            local key="${match[1]}"
            local val="${match[2]}"
            current_task="${current_task}|${key}:${val}"
        fi
    done < "$workflow_file"
    
    [ -n "$current_task" ] && echo "$current_task"
    
    return 0
}

# ============================================
# TASK EXECUTION
# ============================================
execute_task() {
    local workflow_id="$1"
    local task_def="$2"
    local dry_run="${3:-0}"
    
    # Parse task definition
    local task_id=$(echo "$task_def" | tr '|' '\n' | grep "^id:" | cut -d: -f2 | tr -d ' ')
    local command=$(echo "$task_def" | tr '|' '\n' | grep "^command:" | cut -d: -f2-)
    local session=$(echo "$task_def" | tr '|' '\n' | grep "^session:" | cut -d: -f2 | tr -d ' ')
    local timeout=$(echo "$task_def" | tr '|' '\n' | grep "^timeout:" | cut -d: -f2 | tr -d ' ')
    local retries=$(echo "$task_def" | tr '|' '\n' | grep "^retries:" | cut -d: -f2 | tr -d ' ')
    
    [ -z "$timeout" ] && timeout="$DEFAULT_TIMEOUT"
    [ -z "$retries" ] && retries=0
    [ -z "$session" ] && session="current"
    
    log "Executing task: $task_id"
    [ $dry_run -eq 1 ] && log "[DRY RUN] Would execute: $command"
    
    write_to_bus "TASK_START" "workflow=$workflow_id task=$task_id session=$session"
    
    if [ $dry_run -eq 1 ]; then
        echo "{\"task\": \"$task_id\", \"status\": \"dry_run\", \"duration\": 0}" > "$STATE_DIR/$workflow_id/tasks/${task_id}.json"
        return 0
    fi
    
    # Execute command
    local start_time=$(date +%s)
    local task_log="$STATE_DIR/$workflow_id/tasks/${task_id}.log"
    
    if [ "$session" = "current" ]; then
        # Execute in current shell
        if timeout "$timeout" bash -c "$command" > "$task_log" 2>&1; then
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            echo "{\"task\": \"$task_id\", \"status\": \"success\", \"duration\": $duration}" > "$STATE_DIR/$workflow_id/tasks/${task_id}.json"
            write_to_bus "TASK_COMPLETE" "workflow=$workflow_id task=$task_id duration=${duration}s"
            log "Task $task_id completed in ${duration}s"
            return 0
        else
            local exit_code=$?
            echo "{\"task\": \"$task_id\", \"status\": \"failed\", \"exit_code\": $exit_code}" > "$STATE_DIR/$workflow_id/tasks/${task_id}.json"
            write_to_bus "TASK_FAILED" "workflow=$workflow_id task=$task_id exit_code=$exit_code"
            error "Task $task_id failed with exit code $exit_code"
            return 1
        fi
    else
        # Execute in target session via tx injection
        local tx_cmd="cd $(pwd) && $command"
        if ~/agent-unified/skills/recon-bridge/scripts/term_inject.sh inject "$session" "$tx_cmd" 2>/dev/null; then
            log "Command injected to $session"
            # Note: We can't track completion for injected commands easily
            echo "{\"task\": \"$task_id\", \"status\": \"injected\", \"session\": \"$session\"}" > "$STATE_DIR/$workflow_id/tasks/${task_id}.json"
            return 0
        else
            error "Failed to inject command to $session"
            return 1
        fi
    fi
}

# ============================================
# DEPENDENCY RESOLUTION
# ============================================
resolve_dependencies() {
    local workflow_file="$1"
    
    # Extract task dependencies and return execution order
    # Simple topological sort
    local tasks=$(parse_workflow "$workflow_file")
    local order=""
    local completed=""
    
    while [ -n "$tasks" ]; do
        local ready=""
        local remaining=""
        
        while IFS= read -r task; do
            [ -z "$task" ] && continue
            
            local task_id=$(echo "$task" | tr '|' '\n' | grep "^id:" | cut -d: -f2 | tr -d ' ')
            local deps=$(echo "$task" | tr '|' '\n' | grep "^depends_on:" | cut -d: -f2 | tr -d '[] ')
            
            # Check if all dependencies are completed
            local deps_met=1
            if [ -n "$deps" ]; then
                for dep in $(echo "$deps" | tr ',' ' '); do
                    if [[ ! "$completed" =~ "$dep" ]]; then
                        deps_met=0
                        break
                    fi
                done
            fi
            
            if [ $deps_met -eq 1 ]; then
                ready="$ready $task_id"
                completed="$completed $task_id"
                order="$order $task"
            else
                remaining="$remaining\n$task"
            fi
        done <<< "$tasks"
        
        if [ -z "$ready" ]; then
            error "Dependency cycle detected or unresolvable dependencies"
            return 1
        fi
        
        tasks=$(echo -e "$remaining" | grep -v '^$')
    done
    
    echo -e "$order" | grep -v '^$'
}

# ============================================
# WORKFLOW EXECUTION
# ============================================
cmd_run() {
    local workflow_file=""
    local workflow_id=""
    local dry_run=0
    local force=0
    local specific_task=""
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --id) workflow_id="$2"; shift 2 ;;
            --dry-run) dry_run=1; shift ;;
            --force) force=1; shift ;;
            --task) specific_task="$2"; shift 2 ;;
            -*) error "Unknown option: $1"; return 1 ;;
            *) 
                if [ -z "$workflow_file" ]; then
                    workflow_file="$1"
                else
                    error "Unexpected argument: $1"
                    return 1
                fi
                shift
                ;;
        esac
    done
    
    if [ -z "$workflow_file" ]; then
        error "Usage: workflow-runner run <workflow-file> [options]"
        return 1
    fi
    
    [ ! -f "$workflow_file" ] && error "Workflow file not found: $workflow_file" && return 1
    
    # Generate or use provided ID
    [ -z "$workflow_id" ] && workflow_id=$(generate_workflow_id "wf")
    
    log "Starting workflow: $workflow_id"
    log "Workflow file: $workflow_file"
    [ $dry_run -eq 1 ] && log "Mode: DRY RUN"
    
    # Initialize state
    init_workflow_state "$workflow_id" "$workflow_file"
    write_to_bus "WORKFLOW_START" "id=$workflow_id file=$workflow_file dry_run=$dry_run"
    
    # Resolve execution order
    log "Resolving dependencies..."
    local execution_order=$(resolve_dependencies "$workflow_file")
    local task_count=$(echo "$execution_order" | wc -l)
    log "Execution order: $task_count tasks"
    
    # Execute tasks
    local success_count=0
    local failed_count=0
    
    echo "$execution_order" | while IFS= read -r task_def; do
        [ -z "$task_def" ] && continue
        
        # Skip if specific task requested
        if [ -n "$specific_task" ]; then
            local task_id=$(echo "$task_def" | tr '|' '\n' | grep "^id:" | cut -d: -f2 | tr -d ' ')
            [ "$task_id" != "$specific_task" ] && continue
        fi
        
        if execute_task "$workflow_id" "$task_def" "$dry_run"; then
            success_count=$((success_count + 1))
        else
            failed_count=$((failed_count + 1))
            # In a full implementation, handle on_failure routing here
        fi
    done
    
    # Final status
    local end_time=$(date +%s)
    local start_time=$(cat "$STATE_DIR/$workflow_id/status.json" | grep -o '"started": "[^"]*"' | cut -d'"' -f4)
    local start_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$start_time" +%s 2>/dev/null || date -d "$start_time" +%s 2>/dev/null || echo "$end_time")
    local duration=$((end_time - start_epoch))
    
    if [ $failed_count -eq 0 ]; then
        update_workflow_status "$workflow_id" "completed" "\"duration\": $duration, \"tasks_completed\": $success_count"
        write_to_bus "WORKFLOW_COMPLETE" "id=$workflow_id status=success duration=${duration}s tasks=$success_count"
        log "Workflow completed successfully in ${duration}s"
    else
        update_workflow_status "$workflow_id" "failed" "\"duration\": $duration, \"tasks_completed\": $success_count, \"tasks_failed\": $failed_count"
        write_to_bus "WORKFLOW_COMPLETE" "id=$workflow_id status=failed duration=${duration}s failed=$failed_count"
        error "Workflow failed: $failed_count tasks failed"
        return 1
    fi
}

# ============================================
# STATUS & LISTING
# ============================================
cmd_list() {
    log "Active workflows:"
    echo ""
    printf "%-30s %-15s %-10s\n" "WORKFLOW ID" "STATUS" "STARTED"
    printf "%-30s %-15s %-10s\n" "$(echo '──────────────────────────────' | head -c 30)" "$(echo '───────────────' | head -c 15)" "$(echo '──────────' | head -c 10)"
    
    for workflow_dir in "$STATE_DIR"/wf-*; do
        [ -d "$workflow_dir" ] || continue
        
        local workflow_id=$(basename "$workflow_dir")
        local status_file="$workflow_dir/status.json"
        
        if [ -f "$status_file" ]; then
            local status=$(grep -o '"status": "[^"]*"' "$status_file" | cut -d'"' -f4)
            local started=$(grep -o '"started": "[^"]*"' "$status_file" | cut -d'"' -f4 | cut -dT -f1)
            printf "%-30s %-15s %-10s\n" "$workflow_id" "$status" "$started"
        fi
    done
}

cmd_status() {
    local workflow_id=""
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --id) workflow_id="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    
    if [ -z "$workflow_id" ]; then
        error "Usage: workflow-runner status --id <workflow-id>"
        return 1
    fi
    
    local workflow_dir="$STATE_DIR/$workflow_id"
    local status_file="$workflow_dir/status.json"
    
    if [ ! -f "$status_file" ]; then
        error "Workflow not found: $workflow_id"
        return 1
    fi
    
    log "Workflow: $workflow_id"
    cat "$status_file" | python3 -m json.tool 2>/dev/null || cat "$status_file"
}

cmd_cancel() {
    local workflow_id=""
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --id) workflow_id="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    
    if [ -z "$workflow_id" ]; then
        error "Usage: workflow-runner cancel --id <workflow-id>"
        return 1
    fi
    
    update_workflow_status "$workflow_id" "cancelled"
    write_to_bus "WORKFLOW_CANCEL" "id=$workflow_id"
    log "Workflow cancelled: $workflow_id"
}

# ============================================
# TEMPLATES
# ============================================
cmd_template() {
    local template_name="${1:-basic}"
    
    case "$template_name" in
        morning-briefing)
            cat << 'EOF'
name: morning-briefing
version: "1.0"
description: Daily morning briefing workflow

tasks:
  - id: check-calendar
    command: echo "Checking calendar..."
    timeout: 30
    
  - id: generate-briefing
    command: echo "Generating briefing..."
    depends_on: [check-calendar]
    timeout: 120
    
  - id: send-notification
    command: echo "Sending notification..."
    depends_on: [generate-briefing]
    timeout: 30
EOF
            ;;
        multi-agent)
            cat << 'EOF'
name: multi-agent-coordination
version: "1.0"
description: Coordinate multiple agents

tasks:
  - id: agent-claude-task
    command: echo "Claude task"
    session: current
    
  - id: agent-kimi-task
    command: echo "Kimi task"
    session: current
    
  - id: agent-codex-task
    command: echo "Codex task"
    session: current
    
  - id: sync-results
    command: echo "Synchronizing..."
    depends_on: [agent-claude-task, agent-kimi-task, agent-codex-task]
EOF
            ;;
        maintenance)
            cat << 'EOF'
name: system-maintenance
version: "1.0"
description: System maintenance tasks

tasks:
  - id: cleanup-logs
    command: echo "Cleaning logs..."
    timeout: 60
    
  - id: backup-state
    command: echo "Backing up state..."
    depends_on: [cleanup-logs]
    timeout: 300
    retries: 3
    
  - id: health-check
    command: echo "Running health check..."
    depends_on: [backup-state]
    timeout: 60
EOF
            ;;
        *)
            cat << 'EOF'
name: basic-workflow
version: "1.0"
description: A basic example workflow

tasks:
  - id: step-1
    command: echo "Step 1"
    
  - id: step-2
    command: echo "Step 2"
    depends_on: [step-1]
    
  - id: step-3
    command: echo "Step 3"
    depends_on: [step-2]
EOF
            ;;
    esac
}

# ============================================
# MAIN
# ============================================
case "${1:-help}" in
    run)
        shift
        cmd_run "$@"
        ;;
    list|ls)
        cmd_list
        ;;
    status)
        shift
        cmd_status "$@"
        ;;
    cancel|stop)
        shift
        cmd_cancel "$@"
        ;;
    template)
        shift
        cmd_template "$@"
        ;;
    help|--help|-h)
        cat << 'EOF'
workflow-runner: DAG-based workflow execution engine

Usage: workflow-runner [command]

Commands:
  run <file> [options]    Run a workflow
    --id <id>             Specify workflow ID
    --dry-run             Validate without executing
    --force               Force restart (ignore checkpoint)
    --task <name>         Run specific task only
    
  list                    List all workflows
  
  status --id <id>        Show workflow status
  
  cancel --id <id>        Cancel a workflow
  
  template [name]         Output workflow template
    morning-briefing      Daily briefing workflow
    multi-agent           Multi-agent coordination
    maintenance           System maintenance

Examples:
  workflow-runner run my-flow.yaml
  workflow-runner run my-flow.yaml --id my-run-001 --dry-run
  workflow-runner template morning-briefing > morning.yaml
EOF
        ;;
    *)
        error "Unknown command: $1"
        echo "Use 'workflow-runner help' for usage"
        exit 1
        ;;
esac
