# <Repo name>: agent instructions

<!--
Starter AGENTS.md for a repo that uses the SDLC Factory. scripts/install.sh
copies it in only when the repo has no AGENTS.md. Fill in every section; the
factory agents read this file for everything specific to this repo. Pipeline
rules (story workspace, git conventions, definition of done) live in
.claude/factory/RULES.md, so don't repeat them here.
-->

<One paragraph: what this repo is and what kind of work arrives as stories.>

## Stories

- Source: GitHub Issues in `<owner>/<repo>` | Jira project `<KEY>`
- Key prefix: `<PREFIX>` (story keys look like `<PREFIX>-<n>`)

## Layout

| Path | What it holds |
|------|---------------|
|      |               |

## Reference pattern

<The existing code new work should mirror, e.g. a module or folder. Say "none
yet" if the repo is new; the first story then sets the pattern.>

## Commands

    <test command>     # run every test
    <lint command>     # lint and format check

Test framework and locations: <e.g. pytest, tests live in <area>/tests/>

## Coding standards

<e.g. "Python follows .claude/factory/standards/python-style.md", plus
anything repo-specific.>

## Definition of done (additions)

<Anything beyond .claude/factory/RULES.md, e.g. teardown checks for
billable cloud resources.>

## Boundaries (additions)

<Anything beyond .claude/factory/RULES.md, e.g. never apply Terraform
against production.>
