# Shared Skills Registry

Central registry for all agent-shared skills.

## Location
`~/agent-unified/skills/`

## Discovery Paths by Agent

| Agent | Discovery Path | Resolution |
|-------|---------------|------------|
| Claude Code CLI | `~/.agents/skills/` | → `~/agent-unified/skills/` |
| Kimi | `~/.config/agents/skills/` | → `~/agent-unified/skills/` |
| Codex | `~/.config/agents/skills/` | → `~/agent-unified/skills/` |

## Registered Skills

### Core Skills

| Skill | Description | Added |
|-------|-------------|-------|
| `mcp-server-config` | Configure MCP servers for Claude Desktop and CLI | 2026-02-13 |
| `diagnostics` | System diagnostics and health monitoring | - |
| `gog` | Google Workspace CLI (Gmail, Calendar, Drive) | - |

### Productivity Skills

| Skill | Description | Added |
|-------|-------------|-------|
| `clippy` | Microsoft 365/Outlook CLI via Playwright automation | 2026-02-22 |
| `himalaya` | CLI email client (IMAP/SMTP) | 2026-02-22 |

### Project-Specific Skills

| Skill | Description | Added |
|-------|-------------|-------|
| `founder-mode` | Founder-mode morning briefing documentation | 2026-02-22 |

### Recon & Coordination Skills

| Skill | Description | Added |
|-------|-------------|-------|
| `recon-bridge` | Bridge terminal recon (.recon/) to coordination bus | 2026-02-13 |
| `agent-presence` | Agent heartbeat and presence tracking | 2026-02-13 |
| `workflow-runner` | DAG-based workflow execution across sessions | 2026-02-13 |

### Neuro-Symbolic Skills

| Skill | Description | Added |
|-------|-------------|-------|
| `neuro-symbolic-overview` | Getting started with neuro-symbolic AI | - |
| `neuro-symbolic-founder` | Founder mode integration | - |
| `neuro-symbolic-knowledge-graph` | Knowledge graph reasoner | - |
| `neuro-symbolic-ltn` | Logic Tensor Networks | - |
| `neuro-symbolic-patterns` | Design patterns for neuro-symbolic AI | - |
| `neuro-symbolic-testing` | Testing strategies | - |
| `neuro-symbolic-validator` | Rule-based validator | - |

## Skill Structure

Each skill follows the standard structure:
```
skill-name/
├── SKILL.md              # Required: metadata + instructions
├── scripts/              # Optional: executable helpers
├── references/           # Optional: documentation
└── assets/               # Optional: templates, images
```

## Adding a New Skill

1. Create skill directory: `~/agent-unified/skills/my-skill/`
2. Add `SKILL.md` with YAML frontmatter (name, description)
3. Add optional `scripts/`, `references/`, `assets/`
4. Validate: `~/agent-unified/scripts/skill-validate.sh my-skill`
5. Update this registry
6. Package (optional): `cd ~/agent-unified/skills && zip -r my-skill.skill my-skill/`

## Skill Naming

- Lowercase letters, digits, hyphens only
- Verb-led when possible: `gh-address-comments`, `validate-config`
- Namespace by tool when useful: `mcp-server-config`, `kimi-cli-help`

---
*Registry maintained in ~/agent-unified/skills/SKILL_REGISTRY.md*
