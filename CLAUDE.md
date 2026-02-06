# OpenVibe

> A Git-like Thread product for Human + AI agent collaboration

## Quick Start

**Detailed guide**: `docs/CLAUDE-CODE-INSTRUCTIONS.md`

```
Read docs/CLAUDE-CODE-INSTRUCTIONS.md for full workflow.
```

## Current Focus

**Phase 1**: M4 (Team Memory) + M3 (Agent Runtime)

Read `docs/INTENT.md` to understand current goals and scope.

## Agent Teams

This project uses the Agent Teams workflow. To enable:

```json
// settings.json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
```

Common team templates:
- **research-team** - Research/analysis, no code writing
- **implementation-team** - Implementation, requires plan approval
- **review-team** - Code review

## Key Docs

| Document | Content |
|----------|---------|
| `docs/INTENT.md` | Current goals (must read at every session start) |
| `docs/DECISIONS.md` | Decision log |
| `docs/CLAUDE-CODE-INSTRUCTIONS.md` | Full workflow guide |
| `docs/design/M*.md` | Module designs |
| `docs/architecture/*.md` | Architecture designs |

## Constraints

- Only submit complete implementations (no partial work)
- Do not leave TODOs
- New features must have tests
- Two teammates should not edit the same file simultaneously

## Design Principles

1. **Memory First** - Memory is the core value
2. **Configuration over Code** - Configuration-driven
3. **Device as Entity** - Devices are first-class citizens
4. **Thread as Git** - Conversation version control
