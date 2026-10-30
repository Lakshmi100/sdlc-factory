# Review: RETAIL-2 Products CRUD

**Verdict:** APPROVE

Review loop 2. Scope reviewed: `git diff factory/agents-v1...HEAD` and
`git log factory/agents-v1..HEAD`. That is six commits: d165e9b (docs), 8587baf (tests),
89eff3b (implementation), fd6f6c5 (design revision, round 5), b94f399 (tests TC91-TC102)
and 6560c8f (fix). See Rules for the base commit.

## Previous rounds

- **Loop 0** (CHANGES_REQUESTED, 1 must fix). A valid non-ASCII sku such as `"ß" * 40`
  grew to 80 characters when uppercased. The row was committed, then `ProductRead`
  (`max_length=64`) failed response validation, so the request returned 500 and every later
  `GET /products` returned 500 too. The human chose option (b), ASCII-only sku
  (design-feedback round 5). **Resolved in loop 1.**
- **Loop 1** (CHANGES_REQUESTED, 1 must fix). Git did not parse `Jira:` / `Agent:` as
  trailers on any commit, because a blank line separated them from `Co-Authored-By:`. The
  code fix was confirmed. **Resolved in this round.** See Rules.

## Design conformance

Loop 2 changed commit messages only. The tree at HEAD is identical to the tree reviewed in
loop 1 (`git diff 74c7944 HEAD` is empty), so the loop 1 findings stand unchanged:

- **Revised sku rule (design sections 3 and 4, Q7, Q9).**
  - `ProductBase.sku` is `Field(min_length=1, max_length=64, pattern=r"^[!-~]+$")`,
    exactly as the design says.
  - The four-line comment the design asks for is directly above the field, word for word.
  - The `r"\S"` comment sits above `name`, as the revised design asks.
  - `name` and `description` are unchanged.
- **Routes.** `routes.py` is unchanged since 89eff3b, as the revised Impact table says
  ("No change in this revision").
- **Behaviour probed in loop 1 with throwaway calls to `ProductCreate` (not committed).**
  - Rejected with 422: `"A\n"`, `"A\r"`, `"é"`, `"ß" * 40`, `"İ"`, `"A\x00"` and
    fullwidth `"Ａ"`.
  - Accepted: `"~!"` and `"WID-001"`.
  - So pydantic's default Rust regex engine treats `$` as end of string, as design Risks
    says. Because ASCII `upper()` never changes length, the loop 0 defect cannot happen.
- **Unchanged from loop 0, and re-checked:**
  - model (`String(64)` unique and indexed, `Numeric(10, 2)`, timestamps)
  - `ProductInput.price`
  - `ProductRead` (`from_attributes`, `price: float` with its comment)
  - the five endpoints, status codes and detail strings
  - the PUT order of checks (422, then 404, then 409)
  - sku uppercasing in the explicit field copy
  - `main.py` lifespan and router
  - Nothing extra: no PATCH, filtering, pagination or orders link.
- **Doc fixes.** The design renumbers the Decision record to section 7, and the Risks
  section uses the guard test names that are actually in the suite.

## Traceability

`services/products/tests/test_products.py` has 103 tests:
- TC01-TC102 each have a test named `test_tcNN_...`, except TC47.
- There are also two design guard tests.

Plus `test_health.py`.

`make test` (re-run this round): customers 23 passed, products 104 passed, orders 1 passed.
There are no skips and no xfails.

| Test-plan case | Test function | Passing |
|----------------|---------------|---------|
| TC01-TC46 | `test_tc01_...` to `test_tc46_...` (names as listed in loop 0) | yes |
| TC47 | none in products. Covered by the customers CI matrix job and `make test` (customers 23 passed), with zero diff under `services/customers` | yes (by `make test`) |
| TC48-TC90 | `test_tc48_...` to `test_tc90_...` (names as listed in loop 0) | yes |
| design guard | test_guard_create_stores_every_field | yes |
| design guard | test_guard_update_stores_every_field | yes |
| TC91 | test_tc91_create_with_non_ascii_sku_that_grows_returns_422 | yes |
| TC92 | test_tc92_create_with_non_ascii_sku_returns_422 | yes |
| TC93 | test_tc93_create_with_space_inside_sku_returns_422 | yes |
| TC94 | test_tc94_create_with_leading_space_in_sku_returns_422 | yes |
| TC95 | test_tc95_create_with_tab_in_sku_returns_422 | yes |
| TC96 | test_tc96_create_with_punctuation_in_sku_returns_201 | yes |
| TC97 | test_tc97_update_with_non_ascii_sku_that_grows_returns_422 | yes |
| TC98 | test_tc98_update_with_space_inside_sku_returns_422 | yes |
| TC99 | test_tc99_create_with_trailing_space_in_sku_returns_422 | yes |
| TC100 | test_tc100_create_with_del_character_in_sku_returns_422 | yes |
| TC101 | test_tc101_create_with_sku_of_exclamation_mark_returns_201 | yes |
| TC102 | test_tc102_update_with_punctuation_in_sku_returns_200 | yes |

**Loop 0 must fix covered.**
- TC91 (POST) checks for 422 and then calls `assert_no_products`. That helper goes through
  `list_products`, which asserts `GET /products` returns 200 and then `[]`.
- TC97 (PUT) checks for 422, checks that the product is unchanged, and checks that
  `GET /products` returns 200 with `["WID-001"]`.
- The range edges are covered: `"!"` (0x21) by TC101, `"~"` (0x7E) by TC96 and TC102, and
  DEL (0x7F) by TC100.

Acceptance criteria coverage:
- **AC1:** TC01-TC20, TC45, TC49-TC102. TC91-TC102 add the ASCII-only sku rule.
- **AC2:** all five endpoints are covered. TC91 and TC97 add GET list checks after a
  rejected sku.
- **AC3:** 409 by TC18, TC36 and TC85-TC87, 404 by TC25, TC37 and TC40-TC43, and price
  <= 0 giving 422 by TC15-TC17, TC33 and TC34.
- **AC4:** met.

## Test integrity

- **Reword did not touch code or tests.** For every old-to-new pair in the run log
  (ea00393->d165e9b, 7b954b0->8587baf, 98a625c->89eff3b, c5ae56d->fd6f6c5,
  b2ed53e->b94f399, 74c7944->6560c8f) the tree hashes are identical, `git diff <old> <new>`
  is empty, the author and date are unchanged, and the only message change is the removed
  blank line before `Co-Authored-By:`. d165e9b's parent is still bd62fd6.
- **New tests unchanged.** `git diff b94f399 HEAD -- services/products/tests` is empty.
  The implementer's commit 6560c8f touches only `services/products/app/schemas.py`.
- **Earlier tests unchanged.** b94f399 only adds lines to `test_products.py`: three
  constants and TC91-TC102. `git diff 8587baf 89eff3b -- services/products/tests` is empty.
- **Nothing skipped.** There are no `skip` or `xfail` markers.

## Rules (branch, trailers, scope, dependencies)

- **Branch:** `RETAIL-2-products-crud` follows the convention.
- **Trailers:** pass on all six commits. Each message ends with one block, `Jira:`,
  `Agent:`, `Co-Authored-By:`, and `git interpret-trailers --parse` returns all three.
  `%(trailers:key=Jira,valueonly)` returns `RETAIL-2` on every commit, and
  `%(trailers:key=Agent,valueonly)` returns the right role:

  | Commit | Subject | Agent |
  |--------|---------|-------|
  | d165e9b | Design and test plan for products CRUD | claude-code/orchestrator |
  | 8587baf | Failing tests for products CRUD | claude-code/tester |
  | 89eff3b | Implement products CRUD | claude-code/implementer |
  | fd6f6c5 | Restrict sku to printable ASCII after review | claude-code/orchestrator |
  | b94f399 | Failing tests for ASCII-only sku | claude-code/tester |
  | 6560c8f | Allow only printable ASCII in sku | claude-code/implementer |

- **Scope:**
  - Code changes are only under `services/products`.
  - The other changes are the story artefacts under `docs/stories/RETAIL-2/`.
  - The diff is empty for `services/customers`, `services/orders`, `.github`, `ruff.toml`,
    `CLAUDE.md` and every requirements file.
- **Dependencies:** none added. No new imports.
- **Base commit:** the branch is cut from `factory/agents-v1` (bd62fd6), with the human's
  approval. bd62fd6 is out of scope here. If the PR targets `main` before bd62fd6 is
  merged, the PR diff will include it. The PR must say so under Open questions.
- **Not pushed:** `git ls-remote --heads origin RETAIL-2-products-crud` is empty, so the
  reword needs no force-push.
- **Working tree:** `docs/stories/RETAIL-2/run-log.md` (and this file) have uncommitted
  changes. They are not part of the reviewed commits.
- **Commands (re-run this round):** `make test` passes (23 / 104 / 1). `make lint` passes
  ("All checks passed!", 25 files already formatted).

## Must fix

None.

## Suggestions

- **The design asks for an `"A\n"` test, but there is none.** Design Risks ("Regex `$`
  and a trailing newline") says: "Add a test for `"A\n"` so a future switch to
  `regex_engine="python-re"` would be caught". The design boundary table also lists
  `"A\n"`. The test plan has no such case, so no test exists.
  - The behaviour is correct today: I probed it and got 422.
  - With Python's `re`, `$` matches before a final newline, so the anchor would silently
    stop guarding against that one input.
  - Add a TC for `"WID-001\n"` on POST in a follow-up, or record why it was left out in
    the PR.
- **Some rejected inputs are tested on POST only.** The design boundary table says "each
  case is tested on both POST and PUT". For the new sku cases:
  - Both POST and PUT: non-ASCII that grows (TC91, TC97), space inside (TC93, TC98) and
    punctuation (TC96, TC102).
  - POST only: tab, DEL, leading or trailing space, `"CAFÉ-1"` and `"!"`.
  - The validation sits in `ProductBase`, which both request schemas share, so the risk is
    low. Either add the PUT cases or note the deviation in the PR.
- **Loop 0 suggestions still open for the PR:**
  - Trailing zeros (`"19.990"`) and exponent forms (`"1e2"`) are accepted (test-plan Q12).
    List this under Open questions.
  - TC48 is weak evidence of isolation on its own. Its docstring already says so, and no
    change is needed.
- **Any future commits** on this branch must keep the single trailer block form.
- **The PR must list:**
  - the deferred follow-up story (block deleting a product that orders refer to, which
    depends on RETAIL-3)
  - design Q9, now closed by the round 5 decision, as a behaviour change from the
    approved design
  - test-plan Q6, Q11 (still open for name and description), Q12, Q14 and Q15
  - the base-branch note above
