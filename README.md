# SDLC Factory

An agentic software delivery pipeline for Claude Code. A story goes in; a
tested, reviewed pull request comes out, with a human approving the design
before any code is written.

```
/story <KEY>
  1. intake          story saved to docs/stories/<KEY>/story.md (GitHub Issues, Jira, or pasted)
  2. story-reviewer  completeness score out of 100 + questions for the human
     READINESS GATE  score ≥ 80 and no blocking issues → continue; otherwise the
                     human completes the story and it is re-reviewed
  3. architect  ┐    design.md     (contract, data model, risks, open questions)
     tester     ┘    test-plan.md  (written from the story alone, in parallel)
  4. conflict check  where design and test plan disagree = where the story is ambiguous
  5. HUMAN GATE      approve, or give feedback and loop
  6. tester          failing tests from the approved plan
  7. implementer     code until tests and lint pass
  8. reviewer        APPROVE or CHANGES_REQUESTED (up to 2 fix loops)
  9. deliver         branch pushed, PR opened, run-log summary
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
| `.claude/agents/` | story-reviewer, architect, tester, implementer, reviewer |
| `.claude/commands/story.md` | the orchestrator |
| `.claude/factory/RULES.md` | pipeline rules shared by every repo |
| `docs/stories/_templates/` | story review, design, test plan, review templates |
| `standards/python-style.md` | an opt-in Python readability standard |
| `templates/` | starter `AGENTS.md` and PR template for target repos |
| `examples/RETAIL-2/` | a complete run on a sample retail API: 5 design-gate rounds, 2 review loops, about 55 minutes |

## The readiness gate

The story reviewer scores every story on 8 criteria (intent, requirements,
acceptance criteria, constraints, scope, dependencies, freedom from design,
open questions) and checks for blocking issues such as untestable acceptance
criteria. It never fills gaps itself: it writes questions for the story owner.
The aim is to surface gaps before design starts, not at the design gate.
Each repo can add its own constraints and blocking rules in the "Story review"
section of its `AGENTS.md`.

## Roadmap

- Calibrate the readiness threshold against real runs.
- Run headless from GitHub Actions, triggered by an issue label.
