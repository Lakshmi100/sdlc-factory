# Story review: RETAIL-2 Products CRUD

Round 1 · 2026-11-01

## Gate

The orchestrator reads this block. Keep it valid JSON and keep the keys exactly.

```json
{
  "key": "RETAIL-2",
  "round": 1,
  "score": 54,
  "threshold": 80,
  "verdict": "NEEDS_INFO",
  "blocking": [],
  "criteria": {"C1": 4, "C2": 8, "C3": 11, "C4": 6, "C5": 5, "C6": 10, "C7": 5, "C8": 5},
  "questions": 12
}
```

Threshold: 80 (AGENTS.md has no "Story review" section, so no override, no
extra checklist and no extra blocking rules apply; RULES.md default used).

## Scores

| # | Criterion | Score | Max | Evidence (quoted from the story) | Gaps |
|---|-----------|-------|-----|----------------------------------|------|
| C1 | Intent and context | 4 | 10 | "Implement create, read, update, delete and list for products, mirroring services/customers." "Source: jira/stories.csv (row 2)" | No "who" (which client or user calls the products API: the orders service, an admin tool, staff?) and no "why" (-5). Source is a CSV row that is not in the repo and no related docs are linked (-1). |
| C2 | Requirements | 8 | 20 | "sku (unique), name, description (optional), price (decimal, > 0), created_at, updated_at" | (1) "unique" sku is undefined: no format, allowed characters, max length, case sensitivity or whitespace handling, and not said whether sku may change on PUT (-4). (2) name and description: no required/optional rule for name stated beyond the list, no min/max length, no rule for empty or whitespace-only strings, no rule for description "" vs null (-4). (3) "decimal" price: no number of decimal places, no maximum value, no rule for extra decimals (reject or round), no JSON format (number or string) (-4). Status codes, PUT-as-full-replacement and list order are covered by "mirroring services/customers" plus AGENTS.md, so not deducted. |
| C3 | Acceptance criteria | 11 | 25 | "Product fields: ...", "Endpoints: POST /products, GET /products, GET /products/{id}, PUT /products/{id}, DELETE /products/{id}", "Duplicate sku returns 409; missing product returns 404; price <= 0 returns 422", "Tests cover every endpoint and every error case above" | The field list is not pass/fail: no expected result when sku or name is missing, empty or the wrong type (-5). The endpoint list is not pass/fail: no expected status or response body for the success path of each endpoint (-5). Server-set fields (id, created_at, updated_at) have no criterion: what happens to created_at and updated_at on PUT, and whether client-sent values are ignored (-4). The 409/404/422 line is pass/fail. The last bullet restates the definition of done rather than a behaviour (noted, not deducted). No boundary cases (smallest valid price, max lengths) because the limits themselves are missing (counted under C2). |
| C4 | Constraints | 6 | 15 | Nothing in the story. | Security not addressed: whether write endpoints need authentication, and a statement that products hold no personal data (-3). Performance/scale not addressed: expected catalogue size, and whether an unpaginated GET /products is acceptable (-3). Compatibility not addressed: orders (services/orders) will call products over HTTP per AGENTS.md; nothing says what DELETE means for products orders may reference, or that the response shape is a contract for orders (-3). Cost: not stated, but plausibly not applicable (not deducted). AGENTS.md has no story-review checklist. |
| C5 | Scope boundaries | 5 | 10 | "mirroring services/customers" | No out-of-scope list; scope is only implied by the reference to customers (-5). Neighbouring work a reader might assume: pagination/filter/search, stock or inventory, currency, categories, soft delete, orders integration. |
| C6 | Dependencies and inputs | 10 | 10 | "mirroring services/customers" | services/customers exists and is complete (confirmed: app/models.py, schemas.py, routes.py, tests). The target service services/products exists (confirmed). No other dependency is implied. Observation, not deducted: AGENTS.md calls products a "Scaffold (health check only)", but services/products/app already contains a Product model, routes and tests/test_products.py. The story owner should confirm this story is to be (re)delivered against that state. The source CSV is not present (accepted). |
| C7 | Free of design | 5 | 5 | "price (decimal, > 0)", "mirroring services/customers" | No unexplained design. The endpoint paths are the API contract (what). "decimal" and "mirroring" are listed under "Design detail to confirm" below. |
| C8 | Open questions resolved | 5 | 5 | No TBD, open question or contradiction in the story. | None. |
| | **Total** | **54** | **100** | | |

## Blocking issues
| # | Issue | Where in the story |
|---|-------|--------------------|
| - | None. The acceptance criteria are weak (see C3) but each can be tested as written, so B2 does not apply. | |

## Questions for the story owner
Ordered by points recovered, largest first.

| # | Resolves | Question | Why it matters |
|---|----------|----------|----------------|
| Q1 | C3 | For each endpoint, what is the expected success result: status code and response body (e.g. POST 201 with the created product, GET list 200 with an array, DELETE 204 with no body)? Is "same as customers" acceptable as the stated answer? | Without it the tester must infer success outcomes from AGENTS.md rather than the story. |
| Q2 | C3 | What should happen when sku or name is missing, empty, or the wrong type, or when price is missing or not a number: 422 in every case? | Only price <= 0 has a stated error; the tester would otherwise guess the result for every other invalid input. |
| Q3 | C1 | Who uses the products API (the orders service, a back-office/admin user, both?) and what business need does it serve? | Intent drives the architect's choices on validation strictness, response shape and what counts as a breaking change. |
| Q4 | C5 | What is explicitly out of scope? For example: pagination/filtering/search, stock levels, currency, categories, soft delete, any change to orders. | Without a list, the architect and reviewer may disagree on whether these belong in this story. |
| Q5 | C2 | What makes a sku valid and unique: allowed characters, min/max length, is uniqueness case-sensitive ("wid-001" vs "WID-001"), is surrounding whitespace trimmed or rejected, and may sku be changed by PUT? | "unique" with no definition forces the architect to choose case and whitespace rules, and the tester cannot write boundary or duplicate tests. |
| Q6 | C2 | What are the price rules beyond "> 0": how many decimal places, what maximum value, are extra decimals rejected (422) or rounded, and is price sent/returned as a JSON number or a string? | Money precision and format must be fixed for exact-value tests and for orders to consume the price safely. |
| Q7 | C2 | What are the rules for name and description: max length of each, may name be empty or whitespace-only, and should an empty description be stored as "" or as null? | Otherwise limits and empty-string handling are invented by the architect and untestable from the story. |
| Q8 | C3 | Are id, created_at and updated_at always set by the server (client-sent values ignored), and on PUT should created_at stay the same while updated_at changes? | These fields are listed but no behaviour is stated, so the tester cannot write a pass/fail check for them. |
| Q9 | C4 | What should DELETE do for a product that orders may already reference: allow it (hard delete), refuse it, or is this not a concern for this story? Is the product response shape a contract the orders service will rely on? | Orders will call products over HTTP; the architect needs to know what compatibility must be preserved. |
| Q10 | C4 | Roughly how many products are expected, and is it acceptable for GET /products to return all of them unpaginated (as customers does)? | Decides whether pagination is needed now or can be stated as out of scope. |
| Q11 | C4 | Do the write endpoints need authentication or authorisation, and can you confirm products hold no personal data? | Security must be addressed or stated as not applicable before design. |
| Q12 | C1 | Can you link the source (the Jira issue or the CSV) and any related docs, such as a product catalogue spec or the orders story? | The story source is not available in the repo, so nothing can be cross-checked. |

## Design detail to confirm
Design choices found in the story. For each, keep it as a constraint (and add
the reason to the story) or remove it and leave it to the architect.

- "price (decimal, > 0)": the decimal type is presumably required so money is
  stored exactly. Keep it as a constraint and state that reason, or state only
  the precision requirement and leave the type to the architect.
- "mirroring services/customers": a constraint already justified by AGENTS.md
  (the reference pattern). Keep it; no change needed.

## Earlier questions
None: this is round 1.
