#!/usr/bin/env python3
"""
Convert MCP server configurations between Claude Desktop and Claude Code CLI formats.

Usage:
    python convert-config.py <input_file> --from {desktop|cli} --to {desktop|cli} [--output <output_file>]

Examples:
    # Convert Desktop config to CLI format
    python convert-config.py claude_desktop_config.json --from desktop --to cli --output ~/.claude.json
    
    # Convert CLI config to Desktop format (stdout)
    python convert-config.py ~/.claude.json --from cli --to desktop
"""

import argparse
import json
import sys
from pathlib import Path


def desktop_to_cli_server(desktop_server: dict) -> dict:
    """Convert a single server from Desktop to CLI format."""
    cli_server = {
        "type": "stdio",
        "command": desktop_server["command"],
    }
    
    if "args" in desktop_server:
        cli_server["args"] = desktop_server["args"]
    
    if "env" in desktop_server:
        cli_server["env"] = desktop_server["env"]
    
    # Note: "autoApprove" is not supported in CLI format - dropped
    # Note: "description" can be added but isn't in Desktop format
    
    return cli_server


def cli_to_desktop_server(cli_server: dict) -> dict:
    """Convert a single server from CLI to Desktop format."""
    desktop_server = {
        "command": cli_server["command"],
    }
    
    if "args" in cli_server:
        desktop_server["args"] = cli_server["args"]
    
    if "env" in cli_server:
        desktop_server["env"] = cli_server["env"]
    
    # Add empty autoApprove array (common practice)
    desktop_server["autoApprove"] = []
    
    # Note: "type" and "description" fields are CLI-specific - dropped
    
    return desktop_server


def desktop_to_cli(desktop_config: dict) -> dict:
    """Convert Desktop config to CLI format."""
    cli_config = {}
    
    if "mcpServers" in desktop_config:
        cli_config["mcpServers"] = {
            name: desktop_to_cli_server(server)
            for name, server in desktop_config["mcpServers"].items()
        }
    
    # Note: Other Desktop-specific fields (globalSettings, securitySettings, workspaces) are dropped
    
    return cli_config


def cli_to_desktop(cli_config: dict) -> dict:
    """Convert CLI config to Desktop format."""
    desktop_config = {}
    
    # Convert global servers
    all_servers = {}
    
    if "mcpServers" in cli_config:
        all_servers.update({
            name: cli_to_desktop_server(server)
            for name, server in cli_config["mcpServers"].items()
        })
    
    # Also include project-specific servers (flattened)
    if "projects" in cli_config:
        for project_path, project_config in cli_config["projects"].items():
            if isinstance(project_config, dict) and "mcpServers" in project_config:
                for name, server in project_config["mcpServers"].items():
                    # Prefix with project to avoid collisions
                    prefixed_name = f"{Path(project_path).name}-{name}"
                    all_servers[prefixed_name] = cli_to_desktop_server(server)
    
    if all_servers:
        desktop_config["mcpServers"] = all_servers
    
    return desktop_config


def main():
    parser = argparse.ArgumentParser(
        description="Convert MCP config between Desktop and CLI formats"
    )
    parser.add_argument("input_file", help="Input config file")
    parser.add_argument(
        "--from",
        dest="from_fmt",
        choices=["desktop", "cli"],
        required=True,
        help="Input format"
    )
    parser.add_argument(
        "--to",
        dest="to_fmt",
        choices=["desktop", "cli"],
        required=True,
        help="Output format"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing output file instead of overwriting"
    )
    
    args = parser.parse_args()
    
    if args.from_fmt == args.to_fmt:
        print("ERROR: --from and --to formats are the same", file=sys.stderr)
        sys.exit(1)
    
    input_path = Path(args.input_file).expanduser()
    
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    # Read input
    try:
        with open(input_path, "r") as f:
            input_config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Could not read input: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Convert
    if args.from_fmt == "desktop" and args.to_fmt == "cli":
        output_config = desktop_to_cli(input_config)
    else:
        output_config = cli_to_desktop(input_config)
    
    # Handle merge
    if args.merge and args.output:
        output_path = Path(args.output).expanduser()
        if output_path.exists():
            try:
                with open(output_path, "r") as f:
                    existing = json.load(f)
                
                if "mcpServers" in existing and "mcpServers" in output_config:
                    # Merge servers, preferring new config
                    existing["mcpServers"].update(output_config["mcpServers"])
                    output_config = existing
            except json.JSONDecodeError:
                pass  # Overwrite invalid JSON
    
    # Output
    output_json = json.dumps(output_config, indent=2)
    
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(output_json)
        print(f"Converted config written to: {output_path}")
        
        # Print summary
        server_count = len(output_config.get("mcpServers", {}))
        print(f"  Servers: {server_count}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
