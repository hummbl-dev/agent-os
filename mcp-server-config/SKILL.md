---
name: mcp-server-config
description: Configure and manage MCP (Model Context Protocol) servers for Claude Desktop and Claude Code CLI. Use when Kimi needs to add, update, remove, validate, or troubleshoot MCP server configurations across different clients. Handles config file locations, environment variables, server settings, and format conversions between Claude Desktop and Claude Code CLI.
---

# MCP Server Configuration

Manage MCP server configurations for Claude Desktop and Claude Code CLI.

## Quick Start

### Common Tasks

**Add a new MCP server to Claude Desktop:**
```bash
# Edit ~/Library/Application Support/Claude/claude_desktop_config.json
# Add server under "mcpServers" key
```

**Add a project-specific MCP server in Claude Code CLI:**
```bash
# Edit ~/.claude.json
# Add server under "projects.<project_path>.mcpServers"
```

**Add a global MCP server in Claude Code CLI:**
```bash
# Edit ~/.claude.json
# Add server under root "mcpServers" key
```

## Configuration File Locations

| Client | Config File Path |
|--------|-----------------|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Code CLI | `~/.claude.json` |

## Configuration Formats

### Claude Desktop Format
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-name"],
      "env": {
        "ENV_VAR": "value"
      },
      "autoApprove": []
    }
  }
}
```

### Claude Code CLI Format (Global)
```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-name"],
      "env": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

### Claude Code CLI Format (Project-Specific)
```json
{
  "projects": {
    "/path/to/project": {
      "mcpServers": {
        "server-name": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-name"],
          "description": "Optional description"
        }
      },
      "enabledMcpjsonServers": [],
      "disabledMcpjsonServers": []
    }
  }
}
```

## Key Differences

| Feature | Claude Desktop | Claude Code CLI |
|---------|---------------|-----------------|
| Root key | `mcpServers` | `mcpServers` (global) or `projects.<path>.mcpServers` (project) |
| Server `type` field | Not required | Required (`stdio`) |
| `autoApprove` | Supported | Not supported |
| `description` | Not supported | Supported (project-level only) |
| Project-scoped | No | Yes |

## Common MCP Servers Reference

See [references/common-servers.md](references/common-servers.md) for ready-to-use configurations for popular MCP servers:

- GitHub (`@modelcontextprotocol/server-github`)
- PostgreSQL (`@modelcontextprotocol/server-postgres`)
- Filesystem (`@modelcontextprotocol/server-filesystem`)
- Brave Search (`@modelcontextprotocol/server-brave-search`)
- And more...

## Environment Variables

**Security best practices:**
- Never hardcode secrets in config files
- Use environment variable references: `"${ENV_VAR_NAME}"`
- For sensitive values, prompt user or read from `.env` files

**Common env vars by server:**
- GitHub: `GITHUB_PERSONAL_ACCESS_TOKEN`
- Postgres: `POSTGRES_URL`
- Brave Search: `BRAVE_API_KEY`

## Troubleshooting

**Server not appearing:**
1. Validate JSON syntax
2. Check `type: "stdio"` is set for Claude Code CLI
3. Verify command path is absolute or in PATH
4. Check logs: `~/Library/Logs/Claude/` (Desktop) or terminal output (CLI)

**Permission errors:**
1. Ensure config file is readable
2. Check server binary has execute permissions
3. Verify env vars are properly exported

**Connection issues:**
1. Test server manually: run the command directly in terminal
2. Check for port conflicts (for SSE servers)
3. Verify network access for remote servers

## Workflows

### Add a New MCP Server

1. Identify target client (Desktop or CLI)
2. Locate config file
3. Add server entry with unique name
4. Configure command, args, and env vars
5. Validate JSON syntax
6. Restart client to load changes

### Convert Desktop Config to CLI Format

1. Read Desktop config from `claude_desktop_config.json`
2. For each server, add `"type": "stdio"`
3. Remove `autoApprove` field (not supported in CLI)
4. Write to appropriate location in `~/.claude.json`

### Set Up Project-Specific Server

1. Determine absolute project path
2. Ensure project entry exists in `~/.claude.json` `projects` key
3. Add server under `projects.<path>.mcpServers`
4. Optionally add description
5. Restart Claude Code CLI in project directory

## Scripts

Use helper scripts in `scripts/` directory:

- `scripts/validate-mcp-config.py` - Validate MCP config JSON
- `scripts/convert-config.py` - Convert between Desktop/CLI formats

Run with `--help` for usage details.
