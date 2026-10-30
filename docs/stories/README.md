# Story workspaces

Each story run by the factory gets a folder here, e.g. `RETAIL-2/`:

| File                 | Written by    | Purpose                                     |
|----------------------|---------------|---------------------------------------------|
| story.md             | orchestrator  | The story as received from Jira             |
| design.md            | architect     | Analysis, API contract, data model, risks   |
| test-plan.md         | tester (plan) | Independent test cases from the story alone |
| design-feedback.md   | human         | Feedback at the design gate (if any)        |
| review.md            | reviewer      | Verdict, traceability, rule checks          |
| run-log.md           | orchestrator  | Timestamped events, the raw metrics data    |

Run a story with: `/story RETAIL-<n>` in Claude Code.
