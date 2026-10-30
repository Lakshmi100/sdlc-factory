# Test plan: RETAIL-2 Products CRUD

Written from the story only, independently of the design.

Acceptance criteria, numbered for reference:

- AC1: Product fields: id, sku (unique), name, description (optional), price (decimal, > 0), created_at, updated_at
- AC2: Endpoints: POST /products, GET /products, GET /products/{id}, PUT /products/{id}, DELETE /products/{id}
- AC3: Duplicate sku returns 409; missing product returns 404; price <= 0 returns 422
- AC4: Tests cover every endpoint and every error case above

Conventions applied from CLAUDE.md: POST 201, DELETE 204, missing 404, uniqueness 409,
validation 422, PUT is full replacement (all required fields required, omitted optional
fields become null), list ordered by id.

Design-gate decision (round 1, docs/stories/RETAIL-2/design-feedback.md): description stays
optional (omitted or null is valid and stored as null), but a description string, when sent,
must be at least 10 characters. Shorter strings, including "", return 422 on POST and PUT.
Cases TC49-TC54 cover this rule.

Design-gate decisions (round 2, docs/stories/RETAIL-2/design-feedback.md):
- Length limits: sku 1 to 64 characters, name 1 to 200, description 10 to 2000 when present.
  Covered by TC55-TC65.
- Price precision: at most 2 decimal places and at most 10 digits in total (maximum
  99999999.99). Covered by TC66-TC70.
- PUT to a missing id with an invalid body returns 422 only (TC38).
- A sku or name made only of whitespace (e.g. "   ") returns 422 on POST and PUT. Covered by
  TC71-TC74. Values with real characters are stored as sent; no trimming cases are planned.

Design-gate decisions (round 3, docs/stories/RETAIL-2/design-feedback.md):
- PUT minimums: a 1-character sku and a 1-character name are accepted on PUT (200) and
  confirmed on GET. Covered by TC75, TC76.
- A description made only of whitespace (e.g. 10 spaces) is not allowed: 422 on POST and PUT.
  Omitted or null stays valid (TC03, TC04, TC29). Descriptions with real characters are stored
  as sent, no trimming. Covered by TC77, TC78.

Design-gate decisions (round 4, docs/stories/RETAIL-2/design-feedback.md):
- Price is returned as a JSON number (e.g. 19.99, not "19.99") in every response (POST, GET
  by id, GET list, PUT). Requests may send a number or a numeric string. Validation rules are
  unchanged. Covered by TC79-TC83; expected results of TC01, TC02, TC12, TC13, TC27, TC35,
  TC66, TC68 and TC70 now state the JSON number.
- sku is converted to uppercase before saving and is unique regardless of case, on POST and
  PUT. A PUT that changes only the case of the product's own sku succeeds. Other sku rules
  (1-64 characters, whitespace-only rejected, no trimming) are unchanged. Covered by TC84-TC90.
- Deleting a product that orders refer to is out of scope (follow-up story); DELETE stays a
  plain 204 (TC40-TC44 unchanged).

Design-gate decision (round 5, after review loop 0, docs/stories/RETAIL-2/design-feedback.md and
review.md Must fix 1):
- A sku may contain only printable ASCII other than space: letters, digits and punctuation, code
  points 0x21 to 0x7E. Anything else returns 422 on POST and PUT, and nothing is stored or
  changed. This includes non-ASCII letters ("ß", "É"), spaces anywhere (leading, trailing,
  inside), tabs and other control characters (including DEL, 0x7F). Covered by TC91-TC102.
- Regression from review.md: "ß" * 40 used to pass validation, be stored as "SS" * 40
  (80 characters) and make every later GET /products return 500. TC91 and TC97 check that it is
  now 422 and that GET /products still returns 200.
- Effect on existing cases: TC09 and TC71/TC73 (empty and whitespace-only sku, 422) still hold,
  now also for the new reason. Every other existing sku ("WID-001", "GAD-001", "ZZZ-1", "AAA-1",
  "WID-002", "WID-900", "X", "S"*64, "s"*64, "wid-001", "Wid-001") is printable ASCII with no
  space, so no existing case changes. The round 2 note "values with real characters are stored
  as sent" no longer applies to sku values containing spaces: such a sku is now 422, not stored.

Sample data used below: WIDGET = {sku "WID-001", name "Widget", description "A small widget",
price "9.99"}; GADGET = {sku "GAD-001", name "Gadget", price "19.50"}.
Every description string used in a positive case must be at least 10 characters:
"A small widget" (14) and the TC27 replacement "A larger widget" (15) both qualify.
Boundary strings: "Too short" (9 characters) and "Ten chars!" (10 characters).
Length strings are built from ASCII letters: "S"*64 / "S"*65 for sku, "N"*200 / "N"*201 for
name, "D"*2000 / "D"*2001 for description, "X" for the 1-character sku and name cases.
Whitespace-only description: " "*10 (10 ASCII spaces, meets the raw 10-character minimum).
"Stored product unchanged" means a GET after the failed request returns the same sku, name,
description, price and updated_at as before it.
"Price is a JSON number X" means: the response field is a JSON number, not a string (in
Python, `isinstance(body["price"], (int, float))` and not `str`), and its value equals X. Where
exactness matters (TC12, TC68, TC82) the raw response text is also parsed with
`json.loads(..., parse_float=Decimal)` and compared to Decimal(X), so float drift such as
9.9899999 fails. Trailing-zero formatting is not asserted (19.50 and 19.5 are the same number).
sku case: every sample sku above ("WID-001", "GAD-001", "ZZZ-1", "AAA-1", "X", "S"*64) is
already uppercase, so the cases that store "exactly as sent" still hold under the uppercase
rule. Lowercase and mixed-case skus appear only in TC84-TC90.

## Cases
| ID | Covers (AC #) | Type | Scenario | Expected result |
|----|---------------|------|----------|-----------------|
| TC01 | AC1, AC2 | positive | POST /products with WIDGET (every field set) | 201; body has id > 0, sku, name and description equal to the sent values, price is a JSON number 9.99 (sent as "9.99"), and created_at and updated_at present |
| TC02 | AC1 | positive | POST then GET /products/{id}: every field sent on POST is stored | GET returns 200 with sku, name and description equal to the POST values and price as a JSON number 9.99 |
| TC03 | AC1 | positive | POST without description | 201; description is null in POST response and on GET |
| TC04 | AC1 | positive | POST with description explicitly null | 201; description is null |
| TC05 | AC1 | negative | POST without sku | 422 |
| TC06 | AC1 | negative | POST without name | 422 |
| TC07 | AC1 | negative | POST without price | 422 |
| TC08 | AC1 | negative | POST with empty body `{}` | 422 |
| TC09 | AC1 | negative | POST with empty-string sku `""` | 422 |
| TC10 | AC1 | negative | POST with empty-string name `""` | 422 |
| TC11 | AC1 | negative | POST with non-numeric price `"abc"` | 422 |
| TC12 | AC1 | positive | Price is a decimal: POST price "9.99" and read it back | 201; POST response and GET return price as a JSON number 9.99 exactly (raw JSON parsed as Decimal equals Decimal("9.99"); no float drift such as 9.9899999) |
| TC13 | AC1 | positive | Price sent as a JSON number (9.99) is accepted | 201; POST response and GET return price as a JSON number 9.99 |
| TC14 | AC1, AC3 | boundary | POST with smallest plausible positive price "0.01" | 201 |
| TC15 | AC1, AC3 | boundary | POST with price 0 | 422 |
| TC16 | AC1, AC3 | boundary | POST with price "0.00" | 422 |
| TC17 | AC1, AC3 | negative | POST with negative price "-1.00" | 422 |
| TC18 | AC1, AC3 | negative | POST with a second product whose sku is already used | 409; only one product exists afterwards (GET /products length 1) |
| TC19 | AC1, AC3 | positive | POST two products with different skus | Both 201 with different ids |
| TC20 | AC1 | positive | created_at and updated_at are set by the server on create | Both present and parseable as datetimes; a client-sent id/created_at is not honoured (server assigns id) |
| TC21 | AC2 | positive | GET /products with no products | 200; empty list `[]` |
| TC22 | AC2 | positive | GET /products after creating WIDGET then GADGET | 200; list of 2, ordered by id (WID-001 first, GAD-001 second) |
| TC23 | AC2 | positive | GET /products ordering is by id, not by sku or name: create "ZZZ-1"/"Zebra" first, then "AAA-1"/"Aardvark" | List order is ZZZ-1, AAA-1 |
| TC24 | AC2 | positive | GET /products/{id} for an existing product | 200; body matches the created product |
| TC25 | AC2, AC3 | negative | GET /products/999 (not found) | 404 |
| TC26 | AC2 | negative | GET /products/abc (non-integer id) | 422 |
| TC27 | AC2 | positive | PUT /products/{id} with every field changed (new description "A larger widget", 15 chars) | 200; response and subsequent GET show every new value, with price as a JSON number equal to the new price |
| TC28 | AC2 | positive | PUT keeps the same id and the same sku (product updating itself without changing sku) | 200; not treated as a duplicate |
| TC29 | AC2 | positive | PUT without description on a product that had one (full replacement) | 200; description becomes null |
| TC30 | AC2 | negative | PUT without sku | 422 |
| TC31 | AC2 | negative | PUT without name | 422 |
| TC32 | AC2 | negative | PUT without price | 422 |
| TC33 | AC2, AC3 | boundary | PUT with price 0 | 422; stored product unchanged on GET |
| TC34 | AC2, AC3 | negative | PUT with negative price | 422; stored product unchanged on GET |
| TC35 | AC2, AC3 | boundary | PUT with price "0.01" | 200; response and subsequent GET show price as a JSON number 0.01 |
| TC36 | AC2, AC3 | negative | PUT changing a product's sku to one another product already uses | 409; the product's original sku is unchanged on GET |
| TC37 | AC2, AC3 | negative | PUT /products/999 with a valid body | 404 |
| TC38 | AC2, AC3 | negative | PUT /products/999 with an invalid body (price 0) | 422 only; 404 is a failure (resolved at design gate round 2, see Q7) |
| TC39 | AC1, AC2 | positive | PUT changes updated_at but not created_at | created_at equal to value from create; updated_at >= previous updated_at |
| TC40 | AC2 | positive | DELETE /products/{id} for an existing product | 204; empty body; subsequent GET /products/{id} returns 404 |
| TC41 | AC2 | positive | DELETE removes the product from the list only | After deleting WIDGET, GET /products returns only GADGET |
| TC42 | AC2, AC3 | negative | DELETE /products/999 (not found) | 404 |
| TC43 | AC2, AC3 | negative | DELETE the same product twice | First 204, second 404 |
| TC44 | AC1, AC3 | positive | After deleting a product its sku can be reused by a new product | POST with the deleted sku returns 201 |
| TC45 | AC1 | positive | Guard: the test's "every field" data set matches exactly the fields ProductCreate and ProductUpdate accept (mirrors customers guard test) | Sets are equal |
| TC46 | – | regression | GET /health on products service | 200; `{"status": "ok", "service": "products"}` |
| TC47 | – | regression | Customers service test suite still passes unchanged (no edits outside services/products) | `make test` green for customers; customers tests unchanged |
| TC48 | – | regression | Products tests use an isolated in-memory database per test (conftest `client` fixture) | Data created in one test is not visible in another (e.g. TC21 empty list passes regardless of test order) |
| TC49 | AC1 | boundary | POST WIDGET with description "Too short" (9 characters, min-1) | 422; no product created (GET /products returns `[]`) |
| TC50 | AC1 | boundary | POST WIDGET with description "Ten chars!" (exactly 10 characters, min) | 201; description returned and stored on GET as "Ten chars!" exactly |
| TC51 | AC1 | negative | POST WIDGET with empty-string description `""` | 422; no product created (GET /products returns `[]`) |
| TC52 | AC1, AC2 | boundary | PUT an existing WIDGET with a full valid body but description "Too short" (9 characters) | 422; GET shows the product unchanged (description still "A small widget", other fields unchanged) |
| TC53 | AC1, AC2 | boundary | PUT an existing WIDGET with a full valid body and description "Ten chars!" (exactly 10 characters) | 200; response and subsequent GET show description "Ten chars!" |
| TC54 | AC1, AC2 | negative | PUT an existing WIDGET with a full valid body but description `""` | 422; GET shows the product unchanged (description still "A small widget") |
| TC55 | AC1, AC2 | boundary | POST WIDGET with a 64-character sku (max) | 201; sku returned and stored on GET exactly as sent (64 characters) |
| TC56 | AC1, AC2 | boundary | POST WIDGET with a 65-character sku (max+1) | 422; no product created (GET /products returns `[]`) |
| TC57 | AC1, AC2 | boundary | POST WIDGET with a 200-character name (max) | 201; name returned and stored on GET exactly as sent (200 characters) |
| TC58 | AC1, AC2 | boundary | POST WIDGET with a 201-character name (max+1) | 422; no product created (GET /products returns `[]`) |
| TC59 | AC1, AC2 | boundary | POST WIDGET with a 2000-character description (max) | 201; description returned and stored on GET exactly as sent (2000 characters) |
| TC60 | AC1, AC2 | boundary | POST WIDGET with a 2001-character description (max+1) | 422; no product created (GET /products returns `[]`) |
| TC61 | AC1, AC2 | boundary | POST WIDGET with a 1-character sku "X" (min) | 201; sku returned and stored on GET as "X" |
| TC62 | AC1, AC2 | boundary | POST WIDGET with a 1-character name "X" (min) | 201; name returned and stored on GET as "X" |
| TC63 | AC1, AC2 | boundary | PUT an existing WIDGET with a full valid body but a 65-character sku (max+1) | 422; stored product unchanged on GET (sku still "WID-001") |
| TC64 | AC1, AC2 | boundary | PUT an existing WIDGET with a full valid body but a 201-character name (max+1) | 422; stored product unchanged on GET (name still "Widget") |
| TC65 | AC1, AC2 | boundary | PUT an existing WIDGET with a full valid body but a 2001-character description (max+1) | 422; stored product unchanged on GET (description still "A small widget") |
| TC66 | AC1 | positive | POST WIDGET with price "19.99" (2 decimal places) | 201; POST response and GET return price as a JSON number 19.99 |
| TC67 | AC1 | negative | POST WIDGET with price "19.999" (3 decimal places) | 422; no product created (GET /products returns `[]`); not rounded and stored |
| TC68 | AC1 | boundary | POST WIDGET with price "99999999.99" (max: 10 digits, 2 decimals) | 201; POST response and GET return price as a JSON number 99999999.99 exactly (raw JSON parsed as Decimal equals Decimal("99999999.99")) |
| TC69 | AC1 | boundary | POST WIDGET with price "100000000.00" (11 digits, max+0.01) | 422; no product created (GET /products returns `[]`) |
| TC70 | AC1, AC2 | negative | PUT an existing WIDGET with a full valid body but price "19.999" (3 decimal places) | 422; stored product unchanged on GET (price still the JSON number 9.99) |
| TC71 | AC1, AC2 | negative | POST WIDGET with whitespace-only sku "   " | 422; no product created (GET /products returns `[]`) |
| TC72 | AC1, AC2 | negative | POST WIDGET with whitespace-only name "   " | 422; no product created (GET /products returns `[]`) |
| TC73 | AC1, AC2 | negative | PUT an existing WIDGET with a full valid body but whitespace-only sku "   " | 422; stored product unchanged on GET (sku still "WID-001") |
| TC74 | AC1, AC2 | negative | PUT an existing WIDGET with a full valid body but whitespace-only name "   " | 422; stored product unchanged on GET (name still "Widget") |
| TC75 | AC1, AC2 | boundary | PUT an existing WIDGET with a full valid body but a 1-character sku "X" (min) | 200; response and subsequent GET show sku "X" |
| TC76 | AC1, AC2 | boundary | PUT an existing WIDGET with a full valid body but a 1-character name "X" (min) | 200; response and subsequent GET show name "X" |
| TC77 | AC1, AC2 | negative | POST WIDGET with whitespace-only description of 10 spaces " "*10 | 422; no product created (GET /products returns `[]`) |
| TC78 | AC1, AC2 | negative | PUT an existing WIDGET with a full valid body but whitespace-only description of 10 spaces " "*10 | 422; stored product unchanged on GET (description still "A small widget") |
| TC79 | AC1, AC2 | positive | POST WIDGET with price sent as the JSON string "9.99" | 201; POST response price is a JSON number 9.99, not the string "9.99" |
| TC80 | AC1, AC2 | positive | POST WIDGET (price "9.99"), then GET /products/{id} | 200; price is a JSON number 9.99, not a string |
| TC81 | AC1, AC2 | positive | POST WIDGET (price "9.99") and GADGET (price "19.50"), then GET /products | 200; every item's price is a JSON number (not a string); values 9.99 and 19.5 in id order |
| TC82 | AC1, AC2 | boundary | POST WIDGET with price sent as the JSON number 99999999.99 (max) | 201; POST response and GET return price as a JSON number 99999999.99 exactly (raw JSON parsed as Decimal equals Decimal("99999999.99")) |
| TC83 | AC1, AC2 | positive | PUT an existing WIDGET with a full valid body and price sent as the JSON string "19.50" | 200; PUT response and subsequent GET return price as a JSON number 19.5, not a string |
| TC84 | AC1, AC2 | positive | POST WIDGET with lowercase sku "wid-001" | 201; POST response sku is "WID-001"; GET /products/{id} shows sku "WID-001" |
| TC85 | AC1, AC3 | negative | POST WIDGET with sku "wid-001", then POST another product with sku "WID-001" | First 201, second 409; GET /products returns 1 product with sku "WID-001" |
| TC86 | AC1, AC3 | negative | POST WIDGET with sku "WID-001", then POST another product with sku "wid-001" | First 201, second 409; GET /products returns 1 product with sku "WID-001" |
| TC87 | AC2, AC3 | negative | POST WIDGET ("WID-001") and GADGET ("GAD-001"); PUT GADGET with a full valid body and sku "wid-001" | 409; GADGET's sku still "GAD-001" on GET; WIDGET unchanged |
| TC88 | AC1, AC2 | positive | POST WIDGET ("WID-001"); PUT WIDGET with a full valid body and sku "wid-001" (only the case of its own sku changes) | 200 (not 409); PUT response and subsequent GET show sku "WID-001" |
| TC89 | AC1, AC2 | positive | POST WIDGET with mixed-case sku "Wid-001" | 201; POST response and GET show sku "WID-001" |
| TC90 | AC1, AC2 | boundary | POST WIDGET with a 64-character lowercase sku "s"*64 (max) | 201; POST response and GET show sku "S"*64 (64 characters, uppercased) |
| TC91 | AC1, AC2 | regression | POST WIDGET with non-ASCII sku "ß"*40 (40 characters, would become "SS"*40 = 80 characters if uppercased; the review.md defect) | 422 (not 500, not 201); no product created; GET /products returns 200 with `[]` |
| TC92 | AC1, AC2 | negative | POST WIDGET with non-ASCII sku "CAFÉ-1" | 422; no product created (GET /products returns `[]`) |
| TC93 | AC1, AC2 | negative | POST WIDGET with sku "WID 001" (space inside) | 422; no product created (GET /products returns `[]`) |
| TC94 | AC1, AC2 | negative | POST WIDGET with sku " WID-001" (leading space) | 422; no product created (GET /products returns `[]`) |
| TC95 | AC1, AC2 | negative | POST WIDGET with sku "WID-001\t" (trailing tab, a control character) | 422; no product created (GET /products returns `[]`) |
| TC96 | AC1, AC2 | positive | POST WIDGET with sku "wid_001/A.b#~" (letters, digits and punctuation, including "~" = 0x7E, the top of the range) | 201; POST response and GET show sku "WID_001/A.B#~" |
| TC97 | AC1, AC2 | regression | PUT an existing WIDGET with a full valid body but sku "ß"*40 | 422 (not 500, not 200); stored product unchanged on GET (sku still "WID-001"); GET /products returns 200 with the one product |
| TC98 | AC1, AC2 | negative | PUT an existing WIDGET with a full valid body but sku "WID 001" (space inside) | 422; stored product unchanged on GET (sku still "WID-001") |
| TC99 | AC1, AC2 | negative | POST WIDGET with sku "WID-001 " (trailing space) | 422; no product created (GET /products returns `[]`) |
| TC100 | AC1, AC2 | boundary | POST WIDGET with sku "WID-001\x7f" (DEL, 0x7F, one above the top of the range) | 422; no product created (GET /products returns `[]`) |
| TC101 | AC1, AC2 | boundary | POST WIDGET with 1-character sku "!" (0x21, the bottom of the range) | 201; POST response and GET show sku "!" |
| TC102 | AC1, AC2 | positive | PUT an existing WIDGET with a full valid body and sku "wid_001/A.b#~" | 200; PUT response and GET show sku "WID_001/A.B#~" |

Types: positive, negative, boundary, regression.

## Acceptance criteria coverage
| AC # | Criterion | Cases |
|------|-----------|-------|
| AC1 | Product fields: id, sku (unique), name, description (optional), price (decimal, > 0), created_at, updated_at | TC01-TC20, TC39, TC44, TC45, TC49-TC86, TC88-TC102 (description optional: TC03, TC04, TC29; description min length 10: TC49-TC54; length limits sku 1-64, name 1-200, description max 2000: TC55-TC65, TC75, TC76; price precision 2 decimals / 10 digits: TC12, TC66-TC70; whitespace-only sku/name: TC71-TC74; whitespace-only description: TC77, TC78; price returned as a JSON number, sent as number or string: TC01, TC02, TC12, TC13, TC79-TC83; sku uppercased on save: TC84, TC88-TC90; sku unique regardless of case: TC85-TC88; sku printable ASCII only (0x21-0x7E), 422 otherwise: TC91-TC95, TC97-TC100, accepted at the range edges and with punctuation: TC96, TC101, TC102) |
| AC2 | Endpoints: POST, GET list, GET by id, PUT, DELETE | POST: TC01-TC20, TC49-TC51, TC55-TC62, TC66-TC69, TC71, TC72, TC77, TC79, TC82, TC84-TC86, TC89-TC96, TC99-TC101; GET list: TC21-TC23, TC81, TC91, TC97 (still 200 after a rejected non-ASCII sku); GET by id: TC24-TC26, TC80; PUT: TC27-TC39, TC52-TC54, TC63-TC65, TC70, TC73, TC74, TC75, TC76, TC78, TC83, TC87, TC88, TC97, TC98, TC102; DELETE: TC40-TC44 (plain 204; product-referenced-by-orders rule deferred, see Q8) |
| AC3 | Duplicate sku 409; missing product 404; price <= 0 422 | 409: TC18, TC36, TC85, TC86, TC87 (case-insensitive duplicates); 404: TC25, TC37, TC40, TC42, TC43; 422 price: TC15-TC17, TC33, TC34 (boundaries TC14, TC35); 422 wins over 404 for an invalid body on a missing id: TC38 |
| AC4 | Tests cover every endpoint and every error case above | Every endpoint and every AC3 error appears on both POST and PUT where applicable (see rows above) |

## Automation notes
- TC47 is not automated as a products test, because services stay independent (CLAUDE.md).
  It is verified by the customers job in CI (.github/workflows/ci.yml, which runs each
  service's tests separately) and by `make test`, and by the PR diff showing no changes under
  services/customers.

## Questions for the story
1. Resolved (design gate, round 2): sku 1 to 64 characters, name 1 to 200, description 10 to 2000 when present. Covered by TC55-TC65 and TC75-TC76 (max and max+1 on POST, max+1 on PUT, 1-character sku and name on POST and PUT) and TC49-TC54 (description minimum).
2. Resolved (design gate, round 4): sku is converted to uppercase before saving and is unique regardless of case on POST and PUT; a PUT that changes only the case of the product's own sku succeeds. Covered by TC84-TC90. The trimming half was answered at round 2: values with real characters are not trimmed; no trimming case is planned for normal values.
3. Resolved (design gate, round 2): empty-string sku or name is rejected with 422 (TC09, TC10), and a whitespace-only sku or name such as "   " is also rejected with 422 on POST and PUT (TC71-TC74).
4. Resolved (design gate, round 2): price allows at most 2 decimal places and at most 10 digits in total (maximum 99999999.99). A third decimal place is rejected with 422, not rounded. Covered by TC12, TC66-TC70.
5. Resolved (design gate, round 4): price is returned as a JSON number (e.g. 9.99), never a string; requests may send a number or a numeric string. Covered by TC79-TC83, and TC01, TC02, TC12, TC13, TC27, TC35, TC66, TC68, TC70 now assert the JSON number.
6. Can sku be changed via PUT, or is it immutable after creation? The plan assumes it is changeable (TC27, TC36).
7. Resolved (design gate, round 2): PUT on a non-existent id with an invalid body returns 422 only; 404 is not acceptable. TC38 asserts 422.
8. Resolved (design gate, round 4): deferred to a follow-up story (depends on RETAIL-3 orders). In RETAIL-2, DELETE stays a plain delete returning 204 (TC40-TC44); no case covers orders referencing a product.
9. Resolved (design gate, round 1): a description of empty string "" is rejected with 422, not stored and not normalised to null. More generally a sent description must be at least 10 characters; omitted or null remains valid and is stored as null. Covered by TC49-TC54 (POST and PUT).
10. Resolved (design gate, round 3): a description made only of whitespace (e.g. 10 spaces) is not allowed and returns 422 on POST and PUT (TC77, TC78). Omitted or null stays valid (TC03, TC04, TC29). Descriptions with real characters are stored exactly as sent, no trimming; no case asserts how leading or trailing spaces count toward the 10-character minimum (e.g. "  short   "), consistent with the no-trimming decision.
11. Partly resolved (design gate, round 5): sku is printable ASCII only, so characters and bytes are the same for sku. Still open for name and description, which may contain non-ASCII; the plan uses ASCII strings for their length limits (TC57-TC60, TC64, TC65), so it does not depend on the answer.
12. Is a price with a trailing zero beyond the second decimal (e.g. "19.990") treated as 3 decimal places (422) or normalised to 19.99 (accepted)? Similarly, is a JSON number price with 3 decimals (19.999) handled the same as the string form? The plan tests only the string "19.999" (TC67, TC70); no case asserts trailing-zero behaviour.
13. Resolved (design gate, round 5): sku may contain only printable ASCII other than space (0x21-0x7E); anything else is 422 on POST and PUT. Uppercasing ASCII never changes the length, so the 1 to 64 limit gives the same result before and after uppercasing. Covered by TC91-TC102.
14. Must the JSON number keep two decimal places in its text form (19.50 vs 19.5)? JSON treats them as the same number, so the plan compares numerically and does not assert the textual formatting (TC81, TC83).
15. Is the order of checks on a sku that is both too long and non-ASCII (e.g. "ß"*65) important? Both rules give 422, so the plan does not assert which rule reports it.
