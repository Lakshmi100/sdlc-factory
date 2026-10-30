# Retail Factory: agent instructions

This repo is a sandbox for an agentic software factory. Work arrives as Jira
stories in the RETAIL project. Your job is to deliver one story per branch,
fully tested, as a pull request a human can review quickly.

## Layout

Three independent FastAPI microservices, each with its own database:

| Service   | Path                  | Local port | Status                          |
|-----------|-----------------------|------------|---------------------------------|
| customers | services/customers    | 8001       | Complete: the reference pattern |
| products  | services/products     | 8002       | Scaffold (health check only)    |
| orders    | services/orders       | 8003       | Scaffold (health check only)    |

Every service has the same shape:

    app/database.py   engine, Base, get_db dependency
    app/models.py     SQLAlchemy 2.0 models (Mapped / mapped_column)
    app/schemas.py    Pydantic v2 schemas: <Entity>Create, <Entity>Update, <Entity>Read
    app/routes.py     APIRouter with CRUD endpoints
    app/main.py       FastAPI app, lifespan creates tables, /health
    tests/conftest.py in-memory SQLite `client` fixture
    tests/test_*.py   one test per behaviour

## The reference pattern

**Before writing code in products or orders, read services/customers in full
and mirror it.** Same file names, same error handling, same test style.

- POST returns 201, DELETE returns 204, missing resource returns 404,
  uniqueness conflicts return 409, validation errors return 422 (FastAPI default).
- PUT is a full replacement; all fields required.
- List endpoints return results ordered by id.
- Services never share a database or import each other's code. Orders talks
  to customers and products over HTTP only, using httpx and the CUSTOMERS_URL /
  PRODUCTS_URL environment variables. In tests, mock those HTTP calls.

## Coding style

**All code, app and tests, must follow [style.md](style.md). Read it before
writing code.** The aim is code that developers who are not Python experts can
read, without losing quality or performance. In short:

- Plain, explicit code: no lambdas, no `**dict` unpacking, no `setattr`,
  no inline `x if y else z`; comprehensions only in their simplest form.
- One step per line, full-word names, docstrings on every module, class and function.
- Framework constructs (decorators, `Depends`, `yield`, `Mapped`) stay, with a
  `Framework note:` comment the first time they appear in a file.
- Copy fields explicitly, with a comment showing the Python shortcut, and add
  guard tests that fail when a field is missed.
- If a rule would clearly make the code worse, break it with a
  `Style exception:` comment and list it under "Open questions" in the PR.

## Commands

    make install   # install dev deps for all services
    make test      # run every service's tests
    make lint      # ruff check + ruff format --check

To work on one service: `cd services/<name> && python -m pytest -q`

## Definition of done

1. Every acceptance criterion in the story has at least one test.
2. `make test` and `make lint` both pass.
3. Code follows style.md; any `Style exception:` is listed in the PR.
4. No changes outside the service(s) the story names, unless the story says so.
5. PR opened using .github/pull_request_template.md, with every section filled in.

## Git conventions (these feed the factory metrics, so follow them exactly)

- Branch: `RETAIL-<n>-short-description`, e.g. `RETAIL-2-products-crud`
- PR title: `RETAIL-<n>: <story summary>`
- Every commit message ends with these trailers:

      Jira: RETAIL-<n>
      Agent: <tool>/<role>     e.g. claude-code/implementer

  Keep every trailer, including any `Co-Authored-By:` line, in one block at
  the very end of the message, with no blank line between them. Git only
  reads the last paragraph as trailers, so a blank line inside the block
  hides `Jira:` and `Agent:` from the metrics. Check a commit with
  `git log -1 --format='%(trailers:key=Jira,valueonly) %(trailers:key=Agent,valueonly)'`.

## Boundaries

- Never push to main. Never force-push.
- Do not edit .github/workflows, ruff.toml, or this file unless the story asks.
- Do not add dependencies beyond requirements.txt without listing them in the PR.
- If a story is ambiguous or contradicts this file, do not guess silently.
  State the question and the assumption you made under "Open questions" in the PR.
