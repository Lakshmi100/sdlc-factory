# Story review: RETAIL-2 Products CRUD

Round 1 · 2026-11-01

## Gate

The orchestrator reads this block. Keep it valid JSON and keep the keys exactly.

```json
{
  "key": "RETAIL-2",
  "round": 1,
  "score": 57,
  "threshold": 80,
  "verdict": "NEEDS_INFO",
  "blocking": [],
  "criteria": {"C1": 5, "C2": 8, "C3": 12, "C4": 12, "C5": 5, "C6": 5, "C7": 5, "C8": 5},
  "questions": 10
}
```

Threshold: 80 (AGENTS.md has no "Story review" section, so the RULES.md default applies and there are no extra blocking rules or checklist items).

## Scores

| # | Criterion | Score | Max | Evidence (quoted from the story) | Gaps |
|---|-----------|-------|-----|----------------------------------|------|
| C1 | Intent and context | 5 | 10 | "Implement create, read, update, delete and list for products, mirroring services/customers." · "Source: jira/stories.csv (row 2)" | The "what" and the source are present. The "who" and "why" are missing: no user or consumer is named (e.g. the orders service in RETAIL-3/RETAIL-4, which per `services/orders/app/main.py` will validate products over HTTP, or catalogue staff), and no reason or outcome is given. (-5) |
| C2 | Requirements | 8 | 20 | "sku (unique), name, description (optional), price (decimal, > 0), created_at, updated_at" | (a) `sku`: no format, allowed characters, length limit, or case/whitespace rule, so "unique" is undefined (is `abc-1` a duplicate of `ABC-1` or ` abc-1 `?). (-4) (b) `name` and `description`: no min/max length, no rule on empty or blank strings. `services/customers` limits names to 1–100 characters, but "mirroring" does not say which values apply to products. (-4) (c) `price`: "decimal" has no precision/scale (how many decimal places; is `10.005` rejected, rounded or kept?), no maximum, and no JSON representation (number or string). This is money, so it changes the model, the schema and the tests. (-4) |
| C3 | Acceptance criteria | 12 | 25 | "Duplicate sku returns 409; missing product returns 404; price <= 0 returns 422" · "Endpoints: POST /products, GET /products, ..." · "Product fields: ..." · "Tests cover every endpoint and every error case above" | The error-case bullet is pass/fail and covers the 0 / negative boundary. The "Product fields" bullet is a field list, not a pass/fail criterion: no expected result for a missing `sku`/`name`/`price`, an omitted `description`, or a non-numeric price. (-5) Price precision/format (C2 c) has no criterion. (-4) Sku uniqueness has no criterion for case or whitespace variants, or for a PUT that changes a product's sku to one another product already has. (-4) Happy-path status codes, list ordering and PUT semantics are covered by the AGENTS.md conventions that "mirroring services/customers" brings in, so the "Endpoints" bullet is not penalised separately. |
| C4 | Constraints | 12 | 15 | Nothing in the story. | Compatibility with consumers: orders (RETAIL-3/RETAIL-4) will read products over HTTP (`PRODUCTS_URL`), so the product response shape (especially how `price` is serialised) and what happens when a product an order refers to is deleted are applicable, and not addressed. (-3) Security/personal data and performance/scale are not stated but do not change anything in this sandbox service (see Nice to know). AGENTS.md has no story-review checklist. |
| C5 | Scope boundaries | 5 | 10 | "Implement create, read, update, delete and list for products, mirroring services/customers." | No out-of-scope list; scope is only implied by "mirroring". Obvious neighbours a reader might assume: pagination/filtering/search on GET /products, PATCH, stock/inventory, currency, soft delete or archiving, any change to the orders service. (-5) |
| C6 | Dependencies and inputs | 5 | 10 | "mirroring services/customers" | Listed dependency `services/customers` exists (models, schemas, routes, tests confirmed). Implied but not listed: `services/products` already contains a full products CRUD implementation (`app/models.py` with sku/name/description/price, `app/routes.py` with all five endpoints, `tests/test_products.py` of 1364 lines), while AGENTS.md describes products as "Scaffold (health check only)". The story does not say whether to build on, replace, or only verify that code. (-5) |
| C7 | Free of design | 5 | 5 | "mirroring services/customers" · "Endpoints: POST /products, ..." | No unreasoned design. "Mirroring services/customers" is a repo constraint with its reason in AGENTS.md ("the reference pattern"); endpoint paths and status codes are the contract, not design. |
| C8 | Open questions resolved | 5 | 5 | Whole story. | No TBDs, open questions or contradictions in the story itself. |
| | **Total** | **57** | **100** | | |

## Blocking issues
| # | Issue | Where in the story |
|---|-------|--------------------|
| – | None. Every acceptance criterion can be tested as written (the vague ones cost points under C3 but are not untestable), no listed dependency is missing, and nothing asked for is forbidden by AGENTS.md or RULES.md. | – |

## Questions for the story owner
Ordered by points recovered, largest first.

| # | Resolves | Question | Why it matters |
|---|----------|----------|----------------|
| Q1 | C1 | Who needs product CRUD and why: is the main consumer the orders service (RETAIL-3/RETAIL-4), people managing a catalogue, or both? | Tells the architect which response fields and behaviours are load-bearing for consumers, and gives the tester the purpose to judge edge cases against. |
| Q2 | C5 | What is explicitly out of scope? For example: pagination/filtering/search on GET /products, PATCH, stock levels, currency, soft delete, any change to orders. | Without it the architect and tester may disagree on whether, say, GET /products needs pagination or filters. |
| Q3 | C6 | `services/products` already contains a complete products CRUD implementation and tests, although AGENTS.md calls it a scaffold. Should this story build on that code, replace it, or only verify it against these criteria? | Decides whether the work is greenfield, a rewrite, or a review, and what "no changes outside the story" means here. |
| Q4 | C3 | For the field list, what exactly should happen when `sku`, `name` or `price` is missing, when `description` is omitted (null? empty string?), and when `price` is not a number? | Turns the field bullet into pass/fail criteria; otherwise the tester guesses the expected status and response for each case. |
| Q5 | C2 | What is a valid `sku`: allowed characters, maximum length, and is uniqueness case-sensitive and whitespace-sensitive (are `ABC-1`, `abc-1` and ` ABC-1 ` the same sku)? | Changes the column definition, any normalisation, and which inputs the 409 tests must use. |
| Q6 | C2 | What are the length limits for `name` and `description`, and is an empty or blank `name` allowed? | Customers uses 1–100 for names; the tester cannot tell whether products uses the same limits or none. |
| Q7 | C2 | How precise is `price`: how many decimal places, what maximum value, what happens to an input with more decimals (reject with 422, round, or keep), and is it returned as a JSON number or string? | Money precision drives the column type, the schema and boundary tests, and orders will read this value. |
| Q8 | C3 | Can you add a pass/fail criterion for price format, e.g. the expected result for `10.005` and for the maximum allowed price plus one unit? | The precision rule from Q7 needs a concrete boundary test. |
| Q9 | C3 | Should a PUT that changes a product's sku to one another product already has return 409, and should case/whitespace variants of an existing sku return 409 on create? | Uniqueness on update and on near-duplicates is where implementations most often differ; the tester needs the expected result. |
| Q10 | C4 | What should happen when a product is deleted that orders may later refer to (allowed, blocked, or soft-deleted), and is the product JSON shape a contract orders will depend on? | Decides delete semantics and whether the response shape must stay stable for RETAIL-3/RETAIL-4. |

## Nice to know
- Authentication, authorisation and personal data: products hold no personal data and customers has no auth, so not applicable in this sandbox; worth saying "not applicable" in the story.
- Performance and scale: no expected catalogue size; GET /products returning all rows is fine for a sample service.
- "Tests cover every endpoint and every error case above" restates the definition of done in AGENTS.md rather than adding a criterion.
- Whether `sku` may be changed by PUT: AGENTS.md's "PUT is a full replacement; all fields required" and the customers precedent (email is replaceable) imply yes; confirming it would remove any doubt.
- `created_at` / `updated_at` are presumably server-set and ignored if sent by the client, as in customers.
- List ordering by id, 201 on POST and 204 on DELETE come from AGENTS.md conventions and need not be repeated in the story.

## Design detail to confirm
- "mirroring services/customers": keep as a constraint; its reason is already in AGENTS.md ("the reference pattern").
- No other design choices found.

## Earlier questions
None; this is round 1.
