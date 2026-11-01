# Calibration: story reviewer on RETAIL-2

Blind runs of the `story-reviewer` agent on the original RETAIL-2 story
(`examples/RETAIL-2/story.md`). The agent saw only the story, the retail
repo's `AGENTS.md`, the factory rules and the code. It did not see the design,
the test plan or the human feedback from the real run.

| Run | Agent version | Score | Verdict | Blocking | Questions | Nice to know |
|-----|---------------|-------|---------|----------|-----------|--------------|
| [run 1](story-review.run1.md) | first version | 54 | NEEDS_INFO | 0 | 12 | – |
| [run 2](story-review.run2.md) | + relevance rule, implied-dependency check | 57 | NEEDS_INFO | 0 | 10 | 6 |

| Criterion | Run 1 | Run 2 |
|-----------|-------|-------|
| C1 Intent and context | 4 | 5 |
| C2 Requirements | 8 | 8 |
| C3 Acceptance criteria | 11 | 12 |
| C4 Constraints | 6 | 12 |
| C5 Scope boundaries | 5 | 5 |
| C6 Dependencies and inputs | 10 | 5 |
| C7 Free of design | 5 | 5 |
| C8 Open questions resolved | 5 | 5 |

## Did it find what the human had to fill in?

The real run needed 5 rounds of human feedback at the design gate
(`examples/RETAIL-2/design-feedback.md`). Both runs asked about every one
of them before design:

| Real design-gate round | Run 2 question |
|---|---|
| 1. Description minimum length, empty description | Q6, plus Q4 on omitted description |
| 2. Length limits, price precision, whitespace | Q5, Q6, Q7 |
| 3. Minimum lengths on PUT, whitespace-only description | Q6, Q9 |
| 4. Price as a JSON number, sku case, delete with orders | Q7, Q5, Q10 |
| 5. sku character set (non-ASCII) | Q5 ("allowed characters") |

## What the tuning changed

- **Relevance rule:** pagination, authentication and the source link moved
  from questions (and deductions) in run 1 to "nice to know" in run 2.
- **Implied dependencies:** run 2's C6 deduction came from a mismatch in the
  calibration setup, not from the orders link: the scratch repo was built
  from a commit that already contained the finished products code, while its
  `AGENTS.md` still called products a scaffold (run 2, Q3). The orders link
  was still raised, under C4 (Q10). Worth watching on real stories.

## Takeaways

- The verdict is stable (NEEDS_INFO, 54 and 57). Individual criteria moved by
  up to 6 points between runs, so a score close to 80 is not precise. Rely on
  the blocking issues and the questions, not on a 1–2 point margin.
- Recalibrate after the first real stories, especially whether 80 is the
  right threshold for well-written stories.
