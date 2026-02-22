# Common MCP Servers Reference

Ready-to-use configurations for popular MCP servers.

## GitHub

**Package:** `@modelcontextprotocol/server-github`

**Claude Desktop:**
```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
    },
    "autoApprove": []
  }
}
```

**Claude Code CLI:**
```json
{
  "github": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
    }
  }
}
```

**Required env var:** `GITHUB_PERSONAL_ACCESS_TOKEN` (classic PAT with repo access)

---

## PostgreSQL

**Package:** `@modelcontextprotocol/server-postgres`

**Claude Desktop:**
```json
{
  "postgres": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres"],
    "env": {
      "POSTGRES_URL": "postgresql://user:pass@localhost/dbname"
    },
    "autoApprove": []
  }
}
```

**Claude Code CLI:**
```json
{
  "postgres": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres"],
    "env": {
      "POSTGRES_URL": "postgresql://user:pass@localhost/dbname"
    }
  }
}
```

**Required env var:** `POSTGRES_URL` (full connection string)

---

## Filesystem

**Package:** `@modelcontextprotocol/server-filesystem`

**Claude Desktop:**
```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"],
    "autoApprove": []
  }
}
```

**Claude Code CLI:**
```json
{
  "filesystem": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
  }
}
```

**Note:** Pass allowed directories as arguments. Multiple dirs: `["/dir1", "/dir2"]`

---

## Brave Search

**Package:** `@modelcontextprotocol/server-brave-search`

**Claude Desktop:**
```json
{
  "brave-search": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": {
      "BRAVE_API_KEY": "${BRAVE_API_KEY}"
    },
    "autoApprove": []
  }
}
```

**Claude Code CLI:**
```json
{
  "brave-search": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": {
      "BRAVE_API_KEY": "${BRAVE_API_KEY}"
    }
  }
}
```

**Required env var:** `BRAVE_API_KEY` (from https://brave.com/search/api/)

---

## Google Maps

**Package:** `@modelcontextprotocol/server-google-maps`

**Claude Desktop:**
```json
{
  "google-maps": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-google-maps"],
    "env": {
      "GOOGLE_MAPS_API_KEY": "${GOOGLE_MAPS_API_KEY}"
    },
    "autoApprove": []
  }
}
```

**Claude Code CLI:**
```json
{
  "google-maps": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-google-maps"],
    "env": {
      "GOOGLE_MAPS_API_KEY": "${GOOGLE_MAPS_API_KEY}"
    }
  }
}
```

**Required env var:** `GOOGLE_MAPS_API_KEY`

---

## Slack

**Package:** `@modelcontextprotocol/server-slack`

**Claude Desktop:**
```json
{
  "slack": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-slack"],
    "env": {
      "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
      "SLACK_TEAM_ID": "${SLACK_TEAM_ID}"
    },
    "autoApprove": []
  }
}
```

**Claude Code CLI:**
```json
{
  "slack": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-slack"],
    "env": {
      "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
      "SLACK_TEAM_ID": "${SLACK_TEAM_ID}"
    }
  }
}
```

**Required env vars:** `SLACK_BOT_TOKEN`, `SLACK_TEAM_ID`

---

## Memory (Knowledge Graph)

**Package:** `@modelcontextprotocol/server-memory`

**Claude Desktop:**
```json
{
  "memory": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"],
    "env": {
      "MEMORY_FILE_PATH": "${HOME}/.mcp/memory.json"
    },
    "autoApprove": []
  }
}
```

**Claude Code CLI:**
```json
{
  "memory": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"],
    "env": {
      "MEMORY_FILE_PATH": "${HOME}/.mcp/memory.json"
    }
  }
}
```

---

## Fetch

**Package:** `@modelcontextprotocol/server-fetch`

Simple fetch/HTTP request server (no env vars required).

**Claude Desktop:**
```json
{
  "fetch": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-fetch"],
    "autoApprove": []
  }
}
```

**Claude Code CLI:**
```json
{
  "fetch": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-fetch"]
  }
}
```

---

## Sequential Thinking

**Package:** `@modelcontextprotocol/server-sequential-thinking`

For complex multi-step reasoning (no env vars required).

**Claude Desktop:**
```json
{
  "sequential-thinking": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
    "autoApprove": []
  }
}
```

**Claude Code CLI:**
```json
{
  "sequential-thinking": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
  }
}
```

---

## Custom/Local Servers

For locally-built or custom MCP servers:

```json
{
  "my-custom-server": {
    "type": "stdio",
    "command": "/absolute/path/to/server/binary",
    "args": ["--flag", "value"],
    "env": {
      "CUSTOM_VAR": "value"
    }
  }
}
```

**Important:** Use absolute paths for local binaries to avoid PATH issues.
