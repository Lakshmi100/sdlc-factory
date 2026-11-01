# Design feedback: RETAIL-2

## Round 1 (2026-10-25)

Human feedback at the design gate, on conflict C5 (empty-string description):

> for C5 , lets make the Description have a minimum length of atleast 10 chars and add a test for that also

Interpretation applied:
- `description` stays optional: leaving it out or sending null is still valid and stored as null.
- When a description string is sent, it must be at least 10 characters (and at most 2000, as before). Shorter, including `""`, returns 422 on POST and PUT.
- The test plan gets boundary cases for this: 9 characters gives 422, 10 gives 201/200, and `""` gives 422.

## Round 2 (2026-10-25)

Human feedback at the design gate:

> add tests for C1 and C2 , and for C3 the tests should accept only 422 and for C4 , whitespace should not be accepted

Interpretation applied:
- **C1, length limits:** the design's limits are confirmed: sku 1 to 64, name 1 to 200, description 10 to 2000 when present. Add tests at and one past each maximum (64/65, 200/201, 2000/2001) and at the minimum (1-character sku and name accepted), on POST and PUT.
- **C2, price precision:** confirmed: at most 2 decimal places and 10 digits in total (maximum 99999999.99). Add tests: 2 decimal places accepted, 3 decimal places (e.g. "19.999") gives 422, 99999999.99 accepted, 100000000.00 gives 422.
- **C3, TC38:** PUT to a missing id with an invalid body must return 422 only. 404 is no longer an acceptable result.
- **C4, whitespace-only values:** a sku or name made only of whitespace (e.g. "   ") returns 422 on POST and PUT. Values with real characters are stored exactly as sent (no trimming), as the design already says.
- Not covered by this feedback, so unchanged: whether a whitespace-only description of 10+ characters is valid (test-plan Q10). Assumption: accepted, raw length counts.

## Round 3 (2026-10-25)

Human feedback at the design gate:

> Add PUT minimums and make sure sure empty descriptions are not  allowed

Interpretation applied:
- **PUT minimums:** add PUT cases where a 1-character sku and a 1-character name are accepted (200).
- **Empty descriptions:** `""` is already rejected (round 1). Read together with the open gap at this gate, this also means a description made only of whitespace (for example 10 or more spaces) is not allowed: 422 on POST and PUT. Omitted or null is still valid. Descriptions with real characters are stored as sent, no trimming. This closes test-plan Q10 and design Q8.

## Round 4 (2026-10-25)

Human feedback at the design gate:

> lets make Price as a numeric , Sku uniqueness as case-insensitive , and lets make sure deleting a Product is not allowed when orders refer to it

Follow-up answers from the human (asked by the orchestrator):
- Delete rule: **separate story**. Keep a plain delete in RETAIL-2 and record the rule as a follow-up story, like RETAIL-8 does for customers.
- SKU case: **uppercase on save**.

Interpretation applied:
- **Price is a JSON number in responses**, for example `19.99`, not `"19.99"`. Requests still accept a number or a numeric string. The validation rules do not change: greater than 0, at most 2 decimal places and 10 digits. The value is still held as an exact decimal in the schema and the database; only the JSON output changes.
- **sku is unique regardless of letter case** and is converted to uppercase before saving. `"wid-001"` is stored and returned as `"WID-001"`, and creating `"WID-001"` after `"wid-001"` returns 409. The same applies on PUT; a PUT that changes only the case of the product's own sku succeeds. The other sku rules (1 to 64 characters, whitespace-only rejected, no trimming) stay as they are.
- **Deleting a product that orders refer to is out of scope for RETAIL-2.** DELETE stays a plain delete returning 204. The rule becomes a follow-up story once orders exist (it depends on RETAIL-3) and is listed in the PR.

## Round 5: after review loop 0 (2026-10-25)

The reviewer found that a valid non-ASCII sku can grow past 64 characters when uppercased (`"ß" * 40` becomes `"SS" * 40`), which returns 500 and breaks `GET /products` for every client. Human decision:

> Allow only ASCII letters, digits and punctuation in sku (422 otherwise). Update the design, add tests, then fix.

Interpretation applied:
- A sku may contain only printable ASCII characters other than space: letters, digits and punctuation, code points 0x21 to 0x7E. Anything else returns 422 on POST and PUT. This includes non-ASCII letters such as `"ß"` or `"é"`, spaces anywhere (leading, trailing or inside, e.g. `"WID 001"`), tabs and other control characters.
- This replaces the whitespace-only rule for sku: a sku of only spaces is still 422, now for the same reason.
- Uppercasing ASCII never changes the length, so a sku that passes validation always fits `String(64)`.
- name and description are unchanged.
