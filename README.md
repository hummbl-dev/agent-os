# Agent OS

Shared infrastructure for AI agent systems. Used by founder-mode and other projects.

## Overview

Agent OS provides reusable components for building AI agent systems:

- **Skills** - Composable capabilities for AI agents
- **Contracts** - Validated schemas and runtime validators for cross-cutting concerns

## Repository Structure

```
agent-os/
├── skills/              # Agent capabilities (12 skills)
│   ├── agent-presence/    # Agent online/offline detection
│   ├── diagnostics/       # Health monitoring and recovery
│   ├── gog/               # Google Workspace CLI
│   ├── mcp-server-config/ # MCP server management
│   ├── neuro-symbolic-*/  # Neuro-symbolic AI components (7 skills)
│   ├── recon-bridge/      # Terminal reconnaissance bridge
│   └── workflow-runner/   # DAG-based workflow execution
│
├── contracts/           # Cross-cutting contracts (4 domains)
│   ├── cost-governor/     # Budget tracking and policy enforcement
│   ├── health/            # Health check schemas
│   ├── logging/           # Logging standards
│   └── routing/           # Message routing contracts
│
└── SKILL_REGISTRY.md    # Skill index and metadata
```

## Using Agent OS

### As a Git Submodule

```bash
# Add to your project
git submodule add https://github.com/hummbl-dev/agent-os.git agent-os
git submodule update --init --recursive

# Update to latest
cd agent-os
git pull origin main
cd ..
git add agent-os
git commit -m "chore: update agent-os submodule"
```

### Importing Contracts

```python
# Python: Add to path and import
import sys
sys.path.insert(0, 'agent-os/contracts/cost-governor')
from runtime_validator import validator
```

### Using Skills

Each skill has a `SKILL.md` file describing its interface:

```bash
# Read skill documentation
cat agent-os/skills/workflow-runner/SKILL.md
```

## Development

### Adding a New Skill

1. Create directory: `mkdir skills/your-skill-name/`
2. Add `SKILL.md` with specification
3. Update `SKILL_REGISTRY.md`
4. Commit and push

### Adding a New Contract

1. Create directory: `mkdir contracts/your-contract/`
2. Add schema, runtime validator, examples, tests
3. Update dependent projects

## Consumers

| Project | Usage |
|---------|-------|
| [founder-mode](https://github.com/hummbl-dev/founder-mode) | Uses contracts via submodule symlink |

## License

MIT

## Maintainers

- Reuben Bowlby
- Dan Matha
