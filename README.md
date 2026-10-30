# SDLC Factory

An agentic software delivery pipeline for Claude Code. A story goes in; a
tested, reviewed pull request comes out, with a human approving the design
before any code is written.

```
/story <KEY>
  1. intake          story saved to docs/stories/<KEY>/story.md (GitHub Issues, Jira, or pasted)
  2. architect  ┐    design.md     (contract, data model, risks, open questions)
     tester     ┘    test-plan.md  (written from the story alone, in parallel)
  3. conflict check  where design and test plan disagree = where the story is ambiguous
  4. HUMAN GATE      approve, or give feedback and loop
  5. tester          failing tests from the approved plan
  6. implementer     code until tests and lint pass
  7. reviewer        APPROVE or CHANGES_REQUESTED (up to 2 fix loops)
  8. deliver         branch pushed, PR opened, run-log summary
```

Every step is logged with timestamps in `docs/stories/<KEY>/run-log.md`, and
every commit carries `Story:` and `Agent:` trailers, so you can measure the
factory: approval rounds, review loops, escalations, elapsed time.

## Use it on a repo

```bash
./scripts/install.sh /path/to/your-repo
```

This copies the agents, the `/story` command, the pipeline rules and the
templates into the repo. It also creates a starter `AGENTS.md` if the repo
has none. **Fill that in**: it tells the agents where stories come from, the
repo's layout, its test and lint commands, and its coding standards. Then,
in that repo:

```
/story ABC-4
```

Re-run `install.sh` to update a repo to the latest factory. It overwrites
factory files and never touches the repo's own `AGENTS.md`, `CLAUDE.md` or
PR template.

## What's here

| Path | Purpose |
|------|---------|
| `.claude/agents/` | architect, tester, implementer, reviewer |
| `.claude/commands/story.md` | the orchestrator |
| `.claude/factory/RULES.md` | pipeline rules shared by every repo |
| `docs/stories/_templates/` | design, test plan, review templates |
| `standards/python-style.md` | an opt-in Python readability standard |
| `templates/` | starter `AGENTS.md` and PR template for target repos |
| `examples/RETAIL-2/` | a complete run on a sample retail API: 5 design-gate rounds, 2 review loops, about 55 minutes |

## Roadmap

- **Story reviewer:** a first agent that scores a story's completeness before
  design starts, with a gate at 80, so gaps reach the human in round 0 rather
  than at the design gate.
- Run headless from GitHub Actions, triggered by an issue label.
