# Examples

Records of real factory runs, kept unchanged.

- **RETAIL-2** (Oct 25, 2026): Products CRUD on a sample retail FastAPI app.
  The app itself has since been removed from this repo, and this run used the
  earlier Jira-based conventions (`Jira:` trailer, `RETAIL-` keys). It's
  useful for two things:
  - seeing what each agent produces, and
  - calibrating the story reviewer: `story.md` is the story as written, and
    `design-feedback.md` shows the gaps the human had to fill over 5 design-gate
    rounds (length limits, price precision, whitespace, sku case, delete rules).
- **calibration/RETAIL-2/**: blind runs of the story reviewer on the
  RETAIL-2 story, with a comparison against the real design-gate feedback.
