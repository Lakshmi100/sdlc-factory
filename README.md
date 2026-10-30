# Retail Factory

A deliberately small retail backend (customers, products, orders) used as the
workload for learning to build an agentic SDLC "software factory".

The customers service is complete and serves as the reference pattern.
Products and orders are scaffolds: building them is the factory's job, driven
by the Jira stories in jira/stories.csv.

## Quick start

    make install
    make test
    make up        # docker compose: customers :8001, products :8002, orders :8003

Interactive API docs: http://localhost:8001/docs

## Jira setup

1. Create a Jira Cloud project with key **RETAIL**.
2. Import jira/stories.csv (Settings → System → External system import → CSV).
   Import into the empty project so the stories get keys RETAIL-1 … RETAIL-8
   in the order they appear in the file.

## Learning path

| Phase | What you do                                                       |
|-------|-------------------------------------------------------------------|
| 1     | Implement RETAIL-1 interactively with Claude Code; note every intervention |
| 2     | Add subagents (planner, implementer, tester, reviewer) and hooks  |
| 3     | Connect the Atlassian MCP server; run `/implement-story RETAIL-n` |
| 4     | Run headless from GitHub Actions, triggered by a Jira label       |
| 5     | Repeat with GitHub Copilot's coding agent and compare metrics     |
