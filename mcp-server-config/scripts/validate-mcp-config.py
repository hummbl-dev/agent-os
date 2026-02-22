#!/usr/bin/env python3
"""
Validate MCP server configuration files.

Usage:
    python validate-mcp-config.py <config_file> [--format {desktop|cli}]

Examples:
    python validate-mcp-config.py ~/Library/Application\\ Support/Claude/claude_desktop_config.json --format desktop
    python validate-mcp-config.py ~/.claude.json --format cli
"""

import argparse
import json
import sys
from pathlib import Path


def validate_desktop_config(config: dict) -> list[str]:
    """Validate Claude Desktop MCP config format."""
    errors = []
    
    if "mcpServers" not in config:
        errors.append("Missing required key: 'mcpServers'")
        return errors
    
    servers = config["mcpServers"]
    if not isinstance(servers, dict):
        errors.append("'mcpServers' must be an object")
        return errors
    
    for name, server in servers.items():
        if not isinstance(server, dict):
            errors.append(f"Server '{name}' must be an object")
            continue
            
        if "command" not in server:
            errors.append(f"Server '{name}': missing required 'command'")
        
        if "args" in server and not isinstance(server["args"], list):
            errors.append(f"Server '{name}': 'args' must be an array")
        
        if "env" in server and not isinstance(server["env"], dict):
            errors.append(f"Server '{name}': 'env' must be an object")
        
        if "autoApprove" in server and not isinstance(server["autoApprove"], list):
            errors.append(f"Server '{name}': 'autoApprove' must be an array")
    
    return errors


def validate_cli_config(config: dict) -> list[str]:
    """Validate Claude Code CLI MCP config format."""
    errors = []
    
    # Check global mcpServers
    if "mcpServers" in config:
        errors.extend(_validate_cli_servers(config["mcpServers"], "global"))
    
    # Check project-specific servers
    if "projects" in config:
        if not isinstance(config["projects"], dict):
            errors.append("'projects' must be an object")
        else:
            for project_path, project_config in config["projects"].items():
                if not isinstance(project_config, dict):
                    errors.append(f"Project '{project_path}': must be an object")
                    continue
                
                if "mcpServers" in project_config:
                    errors.extend(_validate_cli_servers(
                        project_config["mcpServers"], 
                        f"project '{project_path}'"
                    ))
    
    return errors


def _validate_cli_servers(servers: dict, context: str) -> list[str]:
    """Validate a set of CLI-format MCP servers."""
    errors = []
    
    if not isinstance(servers, dict):
        errors.append(f"[{context}] 'mcpServers' must be an object")
        return errors
    
    for name, server in servers.items():
        if not isinstance(server, dict):
            errors.append(f"[{context}] Server '{name}' must be an object")
            continue
        
        if "type" not in server:
            errors.append(f"[{context}] Server '{name}': missing required 'type' (should be 'stdio')")
        elif server.get("type") != "stdio":
            errors.append(f"[{context}] Server '{name}': type should be 'stdio'")
        
        if "command" not in server:
            errors.append(f"[{context}] Server '{name}': missing required 'command'")
        
        if "args" in server and not isinstance(server["args"], list):
            errors.append(f"[{context}] Server '{name}': 'args' must be an array")
        
        if "env" in server and not isinstance(server["env"], dict):
            errors.append(f"[{context}] Server '{name}': 'env' must be an object")
    
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate MCP server configuration")
    parser.add_argument("config_file", help="Path to the config file")
    parser.add_argument(
        "--format", 
        choices=["desktop", "cli", "auto"],
        default="auto",
        help="Config format (auto-detect if not specified)"
    )
    
    args = parser.parse_args()
    
    config_path = Path(args.config_file).expanduser()
    
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Could not read file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Auto-detect format
    fmt = args.format
    if fmt == "auto":
        if "claude_desktop" in config_path.name or "projects" not in config:
            # Check if servers have "type" field
            has_type = any(
                "type" in server 
                for server in config.get("mcpServers", {}).values()
                if isinstance(server, dict)
            )
            fmt = "cli" if has_type else "desktop"
        else:
            fmt = "cli"
        print(f"Auto-detected format: {fmt}")
    
    # Validate
    if fmt == "desktop":
        errors = validate_desktop_config(config)
    else:
        errors = validate_cli_config(config)
    
    if errors:
        print(f"\nFound {len(errors)} error(s):")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        sys.exit(1)
    else:
        print("✓ Configuration is valid!")
        
        # Print summary
        if fmt == "desktop":
            server_count = len(config.get("mcpServers", {}))
            print(f"  Servers configured: {server_count}")
        else:
            global_count = len(config.get("mcpServers", {}))
            project_count = sum(
                len(p.get("mcpServers", {})) 
                for p in config.get("projects", {}).values()
                if isinstance(p, dict)
            )
            print(f"  Global servers: {global_count}")
            print(f"  Project-specific servers: {project_count}")
        
        sys.exit(0)


if __name__ == "__main__":
    main()
