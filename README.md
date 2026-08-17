# AegisMail Pro

AegisMail Pro is an enterprise email operations platform for SMTP sending, deliverability testing, templates, contacts, logs, and analytics. This repository now includes the **Phase 1 scaffold plus a Phase 2 SMTP sending slice**: real provider connection testing, Celery-backed one-off sends, message lifecycle tracking, and a working messages UI.

## Current scope

This scaffold delivers:

- a monorepo layout for API, worker, web, services, packages, infra, and docs
- a FastAPI backend with clean-architecture folders, auth foundations, RBAC/API key stubs, metrics, health checks, migrations, and seeded demo data
- a Celery worker configured for Redis with real SMTP delivery tasks, retry/backoff behavior, and simple provider throttling
- a Next.js App Router frontend with a premium shell, dark/light mode, command palette stub, SMTP Providers management, sender identity creation, and a messages workspace
- Docker Compose, CI, pre-commit hooks, and setup documentation

## Architecture overview

```text
                        ┌──────────────────────┐
                        │     apps/web         │
                        │ Next.js App Router   │
                        │ UI shell + forms     │
                        └──────────┬───────────┘
                                   │ HTTP
                                   ▼
┌──────────────────────┐  uses  ┌──────────────────────┐  queues  ┌──────────────────────┐
│    services/*        │◄──────►│      apps/api        │─────────►│    apps/worker       │
│ domain boundaries    │        │ FastAPI + SQLAlchemy │          │ Celery + Redis       │
│ smtp/templates/etc.  │        │ Alembic + auth       │          │ retry/backoff tasks  │
└──────────────────────┘        └──────────┬───────────┘          └──────────┬───────────┘
                                           │                                  │
                                           ▼                                  ▼
                                   ┌──────────────┐                    ┌──────────────┐
                                   │ PostgreSQL   │                    │ Redis        │
                                   │ app data     │                    │ broker/cache │
                                   └──────────────┘                    └──────────────┘
```

Monorepo layout:

```text
/apps
  /api
  /worker
  /web
/services
  /smtp
  /templates
  /deliverability
  /imports
  /logging
/packages
  /shared-types
  /ui-components
  /utils
/infra
/docs
```

## Setup

### 1. Clone and configure environment

```bash
git clone <repo-url>
cd aegismail-pro
cp .env.example .env
```

Generate a Fernet key for `APP_ENCRYPTION_KEY` if you need one locally:

```bash
python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
```

### 2. Bring up the stack

```bash
make up
```

### 3. Run migrations

```bash
make migrate
```

### 4. Seed demo data

```bash
make seed
```

The seed script creates:

- a demo admin user
- a demo SMTP provider pointed at Mailpit
- a demo sender identity
- a demo API key

The seed script does **not** print secrets to stdout. The demo admin password comes from `DEFAULT_ADMIN_PASSWORD` in your local `.env`, and the scaffold intentionally suppresses bearer token and API key output from logs.

Mailpit is included in `infra/docker-compose.yml` for local end-to-end demos:

- SMTP endpoint: `localhost:1025`
- inbox UI: `http://localhost:8025`

## Running locally without Docker

### API

```bash
cd apps/api
pip install -e .[dev,test]
alembic upgrade head
uvicorn app.main:app --reload
```

### Worker

```bash
cd apps/worker
pip install -e .
celery -A worker_app.celery_app worker --loglevel=info
```

### Web

```bash
cd apps/web
npm ci
npm run dev
```

## Useful commands

```bash
make up
make down
make migrate
make seed
make test
make lint
```

## Testing

Backend:

```bash
cd apps/api
pytest
```

Frontend:

```bash
cd apps/web
npm run lint
npm run typecheck
npm run test
npm run build
```

## What is implemented today

- [x] Monorepo scaffold with exact top-level structure
- [x] Service READMEs documenting future clean-architecture responsibilities
- [x] FastAPI app with `domain`, `application`, `infrastructure`, and `interfaces`
- [x] SQLAlchemy + Alembic configured via `DATABASE_URL`
- [x] Pydantic settings via `.env`
- [x] JSON logging setup
- [x] `/health`, `/ready`, and `/metrics`
- [x] Initial tables and migration for `users`, `roles`, `api_keys`, `smtp_providers`, `sender_identities`
- [x] Local auth with password hashing + JWT token issue
- [x] RBAC dependency stub and API key auth dependency stub
- [x] SMTP provider create/list/get/update + real SMTP test-connection endpoint
- [x] Sender identity create/list/get
- [x] Encrypted SMTP credentials at rest using the app-level Fernet utility
- [x] `messages` table + migration for one-off delivery tracking
- [x] `POST /messages/send` with idempotency-key support and Celery queue dispatch
- [x] `GET /messages` and `GET /messages/{id}` for status/detail views
- [x] Rate-limit proof endpoint (`/api/v1/auth/login`)
- [x] Pytest coverage for health and SMTP provider CRUD
- [x] Pytest coverage for message queueing, SMTP connection testing, and worker delivery retries/failures
- [x] Celery worker SMTP send task with retry/backoff config and basic per-provider throttling
- [x] Next.js app shell, dark/light mode toggle, command palette stub, placeholder routes
- [x] Reusable SMTP providers data table with sort/filter/paginate/column toggle
- [x] React Hook Form + Zod SMTP provider form posting to the API
- [x] Sender identity creation form and one-off “Send Test Email” flow
- [x] Messages page with status filtering, status badges, and message detail view
- [x] Toast notifications and skeleton loading state
- [x] Vitest + React Testing Library component test
- [x] Docker Compose, Makefile, CI workflow, and pre-commit config
- [x] Seed script for demo data

## Not yet implemented

The following roadmap items are intentionally deferred beyond the current Phase 2 slice:

- [ ] bulk/campaign sending and broader campaign lifecycle management
- [x] template builder, preview renderer, and placeholder validation (Phase 3 — templates CRUD, `{{variable}}` rendering service, version history/rollback, HTML preview, placeholder inspector, extended `/messages/send` with template_id + variables)
- [ ] contacts, lists, suppression models, and import wizard
- [ ] inbox checker execution (only a placeholder route exists; later phases will support **operator-owned seed accounts only**)
- [ ] full logs and analytics dashboards
- [ ] deeper security hardening and full RBAC coverage
- [ ] full data model and remaining migrations
- [ ] deliverability diagnostics and automated guidance

Planned tables tracked for later phases are listed in [`docs/data-model-roadmap.md`](docs/data-model-roadmap.md).

## Known limitations

- Provider throttling is intentionally a simple in-process worker guard suitable for a starting point; it is not yet a distributed/global rate limiter.
- The frontend assumes the API is reachable at `NEXT_PUBLIC_API_BASE_URL`.
- Auth foundations exist, but the web UI does not yet include a full login/session flow.
- The API auto-creates tables on startup for local convenience; Alembic remains the source-of-truth migration path.
- Service and package directories are intentionally lightweight placeholders until later phases need shared runtime code.

## Roadmap

### v3

- bulk/campaign sending orchestration and richer transactional send flows
- richer auth/RBAC coverage and security hardening
- logs and analytics APIs with realistic event ingestion

### v4

- template builder with HTML preview and placeholder intelligence
- contacts/lists/import wizard with validation pipelines
- inbox checker for operator-controlled seed accounts
- broader deliverability tooling, dashboards, and full domain model completion
