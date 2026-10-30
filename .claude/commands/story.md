---
description: Run a story through the SDLC Factory (design, test plan, human gate, tests, implementation, review, PR)
argument-hint: <PREFIX>-<n>
---

You are the orchestrator of the SDLC Factory. Run story **$ARGUMENTS**
through the workflow below. You coordinate; the subagents do the work.
Do not write design, tests or application code yourself.

Read `AGENTS.md` (this repo's conventions) and `.claude/factory/RULES.md`
(pipeline rules) before starting.

Throughout, append a timestamped line to `docs/stories/<KEY>/run-log.md`
at the start and end of every step (format: `2026-01-01T10:00:00Z | step | event | notes`).
Get timestamps with `date -u +%Y-%m-%dT%H:%M:%SZ`. This log feeds the factory metrics.

## 1. Intake
- Create and switch to branch `<KEY>-short-description` from an up-to-date
  default branch.
- If `docs/stories/<KEY>/story.md` does not exist, fetch the story from the
  source `AGENTS.md` names and save it there verbatim, with a first line
  giving its source (URL or key):
  - **GitHub Issues:** `gh issue view <n> --json title,body,labels,url`
  - **Jira:** the Atlassian MCP server, if connected
  - Otherwise, or if fetching fails, ask me to paste the story text.

## 2. Design and test plan (in parallel)
Launch both subagents **in the same message so they run concurrently**:
- `architect` for <KEY>
- `tester` in mode `plan` for <KEY>

## 3. Conflict check
Read design.md and test-plan.md. List where they disagree or where one
covers something the other misses. Disagreement means the story is ambiguous;
that is valuable, so surface it rather than smoothing it over.

## 4. HUMAN GATE: stop here
Show me:
- A short summary of the design and the test plan
- The open questions from both, and the conflicts from step 3
- Paths to both files

Then **stop and wait**. Continue only when I reply "approved".
If I give feedback instead, save it to `docs/stories/<KEY>/design-feedback.md`,
re-run whichever agent it concerns, log a new approval round, and return to this gate.

After approval, commit the docs folder with trailers
`Story: <KEY>` and `Agent: claude-code/orchestrator`.

## 5. Tests first
Launch `tester` in mode `automate`. Confirm the new tests fail and existing
tests pass. Commit the tests with `Agent: claude-code/tester`.

## 6. Implementation
Launch `implementer`. If it escalates a design problem or a disputed test,
stop and bring it to me; do not resolve it yourself.

## 7. Review
Launch `reviewer`. If the verdict is CHANGES_REQUESTED, send the implementer
back with review.md (maximum 2 loops), then review again. If still not
approved after 2 loops, stop and bring it to me.

## 8. Deliver
Push the branch and open a PR with `gh pr create` using
`.github/pull_request_template.md`. In the PR body, link the story, the design,
test plan and review files, and fill "Author" with the agents involved.
Add a final summary to run-log.md: approval rounds, review loops,
escalations, and total elapsed time.
