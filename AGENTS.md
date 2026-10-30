# SDLC Factory: instructions for working on the factory

This repo is the factory itself: the agents, the `/story` orchestrator, the
pipeline rules and templates. It holds no application code. The factory is
installed into target repos with `scripts/install.sh`, and stories run there.

## Layout

| Path | What it holds |
|------|---------------|
| `.claude/agents/` | Subagents: architect, tester, implementer, reviewer |
| `.claude/commands/story.md` | The `/story` orchestrator |
| `.claude/factory/RULES.md` | Pipeline rules every target repo gets: story workspace, git conventions, definition of done, boundaries |
| `docs/stories/_templates/` | Templates for design, test plan, review |
| `standards/` | Reusable coding standards a target repo can opt into from its `AGENTS.md` |
| `templates/` | Starter `AGENTS.md` and PR template for target repos |
| `scripts/install.sh` | Installs or updates the factory in a target repo |
| `examples/` | Real story runs, kept as reference and as calibration data |

## Rules for changing the factory

- **Keep the agents generic.** Nothing about one target repo (its paths,
  languages, commands, cloud) goes into `.claude/`. Agents get those from the
  target repo's `AGENTS.md`. If an agent needs a new kind of repo fact, add a
  section for it to `templates/AGENTS.target.md`.
- **Pipeline rules live in one place:** `.claude/factory/RULES.md`. Agents
  point to it; they don't repeat it.
- **Output files are a contract.** If you change what an agent writes, update
  its template in `docs/stories/_templates/` and every agent that reads it.
- **Don't edit `examples/`.** They are records of real runs.
- Test a change by installing into a scratch repo
  (`./scripts/install.sh /path/to/scratch`) and running a story there.
