# Design: RETAIL-2 Products CRUD

## 1. Analysis
Replace the products scaffold with full CRUD for a `Product` entity (sku, name,
optional description, price), built the same way as `services/customers`:
same files, same error handling (404 / 409 / 422), same test style, and the
style.md rules (explicit field copying with guard tests, `Framework note:`
comments, docstrings everywhere).
Out of scope: stock levels, categories, pagination, filtering or search, PATCH,
and any link to orders. In particular, **blocking the delete of a product that
orders refer to is deferred to a follow-up story** (it depends on RETAIL-3);
DELETE in RETAIL-2 is a plain delete. No other service changes.

**Revision after review loop 0 (design-feedback round 5):** sku is restricted
to printable ASCII other than space (0x21 to 0x7E). This fixes review Must fix 1,
where a non-ASCII sku grew past 64 characters when uppercased and caused a 500.

## 2. Impact
| Service  | Files | Change |
|----------|-------|--------|
| products | `app/models.py` | New. `Product` model and `utcnow()` helper, mirroring `customers/app/models.py`. |
| products | `app/schemas.py` | New. `ProductBase`, `ProductInput`, `ProductCreate`, `ProductUpdate`, `ProductRead` (arrangement in section 4). Revision: the sku `pattern` changes to `r"^[!-~]+$"`. |
| products | `app/routes.py` | New. `APIRouter(prefix="/products", tags=["products"])`, `find_product_or_404`, `save_or_409`, five endpoints. Uppercases sku in the explicit field copy. No change in this revision. |
| products | `app/main.py` | Replace the scaffold docstring. Add the `lifespan` that runs `create_all`, and `include_router(router)`. Keep `/health` as it is. |
| products | `tests/conftest.py` | New. In-memory SQLite `client` fixture, copied from customers. |
| products | `tests/test_products.py` | New. One test per behaviour, plus the three guard tests (style.md section 6). Revision: add the sku character-set cases (section 5 boundary table). |
| products | `tests/test_health.py` | No change. |

No new dependencies. `pydantic` and `sqlalchemy` already provide `Decimal` / `Numeric`.

## 3. API contract
All endpoints are under `/products`. Bodies are JSON.

**Request body (`ProductCreate` and `ProductUpdate`, which are the same):**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| sku | string | yes | 1 to 64 characters. **Every character must be printable ASCII other than space (code points 0x21 to 0x7E): letters, digits and punctuation.** Anything else gives 422: non-ASCII letters (`"ß"`, `"é1"`), a space anywhere (`"WID 001"`, `" WID"`, `"   "`), tabs, newlines and other control characters. Converted to uppercase before saving; unique regardless of case. |
| name | string | yes | 1 to 200 characters; must contain at least one non-whitespace character (`"   "` gives 422) |
| description | string or null | no (default null) | null or omitted is valid; a string must be 10 to 2000 characters and contain at least one non-whitespace character (`""`, anything under 10, and whitespace only such as 10 spaces give 422) |
| price | JSON number or numeric string | yes | `> 0`, at most 10 digits in total, at most 2 after the decimal point (maximum 99999999.99) |

Apart from the sku uppercasing, values that pass validation are stored exactly
as sent. Nothing is trimmed: `" Widget "` is stored and returned as
`" Widget "`. (sku cannot contain spaces, so trimming never applies to it.)

**Response body (`ProductRead`):** every request field, plus `id` (int),
`created_at` (ISO 8601 datetime) and `updated_at` (ISO 8601 datetime).
- **`price` is a JSON number**, for example `19.99`, whether the request sent
  `19.99` or `"19.99"`. `"19.9"` comes back as `19.9`.
- **`sku` is always uppercase**: `"wid-001"` is returned as `"WID-001"`.

| Method | Path | Success | Errors |
|--------|------|---------|--------|
| POST | `/products` | 201, `ProductRead` | 409 sku already used by any product, compared case-insensitively (`"SKU already in use"`); 422 invalid body (any constraint above, including a sku with a character outside 0x21 to 0x7E) |
| GET | `/products` | 200, `list[ProductRead]` ordered by id ascending; `[]` when there are none | none |
| GET | `/products/{product_id}` | 200, `ProductRead` | 404 (`"Product not found"`); 422 for a non-integer id |
| PUT | `/products/{product_id}` | 200, `ProductRead` | 422 invalid body (any constraint above, including a sku with a character outside 0x21 to 0x7E), whether or not the id exists; 404 valid body but missing id; 409 when the sku, in any case, belongs to another product |
| DELETE | `/products/{product_id}` | 204, no body | 404 |

Notes:
- PUT is a full replacement. All required fields must be sent, and leaving out
  `description` sets it to null. A PUT that keeps the product's own sku
  succeeds, including one that changes only its case (`"wid-001"` to
  `"Wid-001"`): both are stored as `"WID-001"`, so it does not conflict with
  itself.
- Creating `"WID-001"` after `"wid-001"` returns 409. The same holds on PUT.
- **PUT to a missing id with an invalid body returns 422, never 404.** FastAPI
  validates the body before the endpoint runs, so the id lookup never happens.
  Order of checks on PUT: body validation (422), then id lookup (404), then sku
  uniqueness (409).
- Error bodies use the FastAPI default: `{"detail": "..."}`.

## 4. Data model
New table `products`. Existing rows: none, because the table does not exist yet.
`create_all` in `lifespan` creates it on start-up.

| Column | SQLAlchemy | Notes |
|--------|------------|-------|
| id | `Integer, primary_key=True` | |
| sku | `String(64), unique=True, index=True` | Always stored uppercase, so this plain unique constraint enforces case-insensitive uniqueness. No functional index. `save_or_409` turns `IntegrityError` into 409. ASCII-only input means the stored value is never longer than 64. |
| name | `String(200)` | |
| description | `Text`, `Mapped[str \| None]` | Nullable. |
| price | `Numeric(10, 2)`, `Mapped[Decimal]` | Exact storage. |
| created_at | `DateTime(timezone=True), default=utcnow` | |
| updated_at | `DateTime(timezone=True), default=utcnow, onupdate=utcnow` | |

**Schema classes.** Request and response need different price types, so price
moves out of the shared base:

    class ProductBase(BaseModel):          # fields shared by every schema
        sku: str = Field(min_length=1, max_length=64, pattern=r"^[!-~]+$")
        name: str = Field(min_length=1, max_length=200, pattern=r"\S")
        description: str | None = Field(default=None, min_length=10, max_length=2000, pattern=r"\S")

    class ProductInput(ProductBase):       # fields a client sends
        price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)

    class ProductCreate(ProductInput): ... # body for POST
    class ProductUpdate(ProductInput): ... # body for PUT

    class ProductRead(ProductBase):        # response
        model_config = ConfigDict(from_attributes=True)
        id: int
        price: float
        created_at: datetime
        updated_at: datetime

`ProductRead` does not inherit from `ProductInput`, so no field is redefined in
a subclass. The price constraint is written once, in `ProductInput`. The
implementer adds a comment on `ProductRead.price` saying it is `float` only so
the JSON shows a number; the exact value lives in the database and in
`ProductInput` (see Decision record).

**sku character set: `pattern=r"^[!-~]+$"` on `Field`.** `!` is 0x21 and `~`
is 0x7E, so `[!-~]` is every printable ASCII character except space: letters,
digits and punctuation. `^` and `$` anchor it, so every character must be in
that range. The implementer writes this comment directly above the sku field:

    # sku may contain only printable ASCII other than space: "!" (0x21) to "~" (0x7E),
    # i.e. letters, digits and punctuation. Spaces, tabs, control characters and
    # non-ASCII letters are rejected (422). ASCII upper() never changes length,
    # so an uppercased sku still fits String(64).

Verified by the orchestrator on pydantic 2.10.4: accepts `"WID-001"`,
`"wid_001/A.b#"`, `"~!"`; rejects `"ß"`, `"é1"`, `"WID 001"`, `" WID"`,
`"   "`, `"A\t"`. This replaces the earlier `r"\S"` on sku; a sku of only spaces
is still 422, now because space is outside the range.

**Whitespace-only check for name and description: `pattern=r"\S"` on
`Field`.** `Field(...)` is already a listed framework construct, so neither
pattern adds a new construct. Pydantic v2 checks `pattern` as a search, not a
full match, so `\S` means "contains at least one non-whitespace character"
(`"   "` is rejected, `" a "` is accepted). The value is not changed, so no
trimming happens. The implementer adds a one-line comment above `name` saying
exactly that. A null or omitted description still passes, because length and
pattern limits apply only to strings (verified on pydantic 2.10.4).

**sku uppercasing happens in the routes, in plain Python**, inside the explicit
field copy: `sku=payload.sku.upper()` in `create_product`, and
`product.sku = payload.sku.upper()` in `update_product`, each with a comment
saying why (stored uppercase so the unique column is case-insensitive). No
schema validator or transform is added. Validation runs on the value as sent.
Because the sku is ASCII, `upper()` maps each character to exactly one
character, so the length is unchanged and the result still passes
`ProductRead`'s `max_length=64` and fits `String(64)`. Every other field is
copied by name as sent, with the "Python shortcut" comment that style.md
section 6 requires.

## 5. Risks
- **Field silently not copied.** Explicit copying can drop a new field. The
  guard tests catch it: `test_tc45_guard_data_covers_every_schema_field`,
  `test_guard_create_stores_every_field` and
  `test_guard_update_stores_every_field` (named after the customers guards,
  with the `tc45_` / `guard_` prefixes used in this suite), using a fixture
  such as `WIDGET_WITH_EVERY_FIELD`. For the round trip to compare equal, that
  fixture uses an already uppercase ASCII sku, price as a JSON number with two
  decimal places (for example `19.99`), and a description of at least 10
  characters with real characters. Lowercase sku and string price get their
  own tests.
- **Comparing price in tests.** Responses return a number, so tests compare
  with numbers (`== 19.99`). Add a test that `"19.99"` sent as a string comes
  back as the number `19.99`.
- **float on output.** `ProductRead.price` converts the stored `Decimal` to
  `float` only for the JSON. Every allowed value (at most 10 digits) is within
  float's 15 significant digits, so the JSON text is exact; `19.99` and
  `99999999.99` were checked on pydantic 2.10.4. Clients that do arithmetic on
  the number get float behaviour; that is the human's choice (design-feedback
  round 4).
- **SQLite and Decimal.** SQLite has no native decimal type, and SQLAlchemy
  logs a warning about it. `Numeric(10, 2)` still gives back a `Decimal`
  rounded to 2 places. Fine at this precision; pytest does not treat warnings
  as errors.
- **The unique sku must hold on PUT as well as POST.** Test: duplicate on POST
  in a different case (409), duplicate on PUT in a different case (409), PUT
  keeping its own sku (200), PUT changing only the case of its own sku (200,
  returned uppercase), and lowercase sku on POST returned uppercase.
- **Non-ASCII sku (corrected after review loop 0).** The earlier version of
  this design said an over-long uppercased sku was harmless on SQLite. That was
  wrong. Python's `upper()` lengthens some characters (`"ß"` becomes `"SS"`),
  so `"ß" * 40` was stored as 80 characters; SQLite accepted the row, but
  `ProductRead` (which inherits `max_length=64`) failed response validation, so
  the request returned 500 and every later `GET /products` returned 500 too
  (review.md Must fix 1). On a database that enforces VARCHAR length it would
  be a 500 at commit instead. The ASCII-only pattern closes this: ASCII
  uppercasing never changes length. Regression test: POST a 40-character `"ß"`
  sku gets 422, and `GET /products` still returns 200 afterwards; the same on
  PUT.
- **Regex `$` and a trailing newline.** In Python's `re`, `$` also matches
  before a final `"\n"`. Pydantic's default regex engine (Rust) treats `$` as
  end of string, so `"A\n"` is rejected. Add a test for `"A\n"` so a future
  switch to `regex_engine="python-re"` would be caught.
- **Boundary values (human-confirmed, design-feedback rounds 2, 3 and 5).**
  Each case is tested on both POST and PUT: each 422 case gives 422 on both,
  and each accepted case gives 201 on POST and 200 on PUT (including the
  1-character sku and name minimums on PUT).

  | Field | Accepted | Rejected with 422 |
  |-------|----------|-------------------|
  | sku | 1 character; 64 characters; `"WID-001"`; `"wid_001/A.b#"` (stored as `"WID_001/A.B#"`); `"~!"` | `""`; missing; 65 characters; `"   "`; `" WID"`; `"WID 001"`; `"A\t"`; `"A\n"`; `"ß"`; `"é1"`; `"ß" * 40` (then `GET /products` still 200) |
  | name | 1 character; 200 characters; `" Widget "` (stored as sent) | `""`; missing; 201 characters; `"   "` |
  | description | omitted or null (stored as null); 10 characters; 2000 characters; `"  a widget  "` (stored as sent) | `""`; 9 characters; 2001 characters; 10 spaces (whitespace only) |
  | price | `0.01`; `"19.99"` (returned as `19.99`); `99999999.99` (returned as `99999999.99`) | `0`; negative; `"19.999"` (3 decimal places); `100000000.00` (11 digits) |

  Plus: PUT with an invalid body to a missing id returns 422 (assert 422 only).
  The earlier accepted case `" A1 "` for sku is now rejected (contains spaces);
  any existing test that expects it to be stored as `" A1 "` must change to
  expect 422.

## 6. Open questions
| # | Question | Recommended assumption |
|---|----------|------------------------|
| 1 | How should price be serialised in responses: as a JSON number or a string? | **Closed (human decision, design-feedback round 4).** JSON number, for example `19.99`. Requests accept a number or a numeric string; validation and `Numeric(10, 2)` storage unchanged. Mechanism: `ProductRead.price: float` (Decision record). |
| 2 | How much precision may price have? | **Closed (human-confirmed, design-feedback round 2).** At most 2 decimal places and 10 digits in total, maximum 99999999.99. More gives 422. |
| 3 | Length limits for sku, name and description? | **Closed (human-confirmed, design-feedback round 2).** sku 1 to 64, name 1 to 200, description 10 to 2000 when present. |
| 4 | Is sku uniqueness case-sensitive? | **Closed (human decision, design-feedback round 4).** Case-insensitive. sku is uppercased before saving (in the routes), so the existing unique column enforces it. No trimming (round 2). |
| 5 | Should deleting a product be blocked once orders reference it? | **Closed (human decision, design-feedback round 4).** Deferred to a follow-up story, depends on RETAIL-3. RETAIL-2 keeps a plain delete returning 204; the follow-up is listed in the PR. |
| 6 | Is an empty-string description allowed? | **Closed (human decision, design-feedback round 1).** No. Description stays optional (omitted or null is stored as null), but a string must be 10 to 2000 characters; `""` and shorter strings return 422 on POST and PUT. |
| 7 | Are whitespace-only sku or name values allowed? | **Closed (human decisions, design-feedback rounds 2 and 5).** No: 422 on POST and PUT. For name, via `pattern=r"\S"`; values with real characters are stored as sent. For sku, superseded by round 5: no whitespace is allowed anywhere, via `pattern=r"^[!-~]+$"`. |
| 8 | Is a whitespace-only description of 10+ characters valid? | **Closed (human decision, design-feedback round 3).** No: 422 on POST and PUT, via the same `pattern=r"\S"`. Omitted or null stays valid; descriptions with real characters are stored as sent, no trimming. |
| 9 | Should sku be limited to characters whose uppercase form has the same length (for example ASCII only)? | **Closed (human decision, design-feedback round 5).** Yes. sku allows only printable ASCII other than space (0x21 to 0x7E); anything else is 422 on POST and PUT. The earlier assumption ("no extra rule, harmless on SQLite") was wrong: it caused a 500 and broke `GET /products` (review.md Must fix 1). ASCII uppercasing never changes length, so a valid sku always fits 64 characters. |

## 7. Decision record: price type and wire format
**Context.** Price is money, so it must be validated and stored exactly and
must be `> 0`. The human decided (round 4) that responses show it as a JSON
number, not a string.
**Storage and input.** `Decimal` with `Field(gt=0, max_digits=10,
decimal_places=2)` in `ProductInput`, `Numeric(10, 2)` in the database.
Rejected: `float` end to end (binary rounding in validation and storage) and
integer cents (contradicts the story's "decimal", makes clients convert).
**Output options.** (a) `ProductRead.price: float`, with `ProductRead` built
from `ProductBase` rather than the input schema. (b) Keep `Decimal` and add
`Annotated[Decimal, PlainSerializer(float, return_type=float,
when_used="json")]`.
**Decision.** (a). It uses only `BaseModel` and a plain type annotation, both
already allowed by style.md section 5. (b) works (checked on pydantic 2.10.4)
but brings in `Annotated` and `PlainSerializer`, which are not in style.md's
table of framework constructs and would need a style exception.
**Consequences.** Validation and storage stay exact. The JSON shows `19.99`.
The conversion to float happens only when building the response, and every
allowed value is exact at float precision. The cost is that price is declared
twice (input and response) with different types, which the comment on
`ProductRead.price` explains.
