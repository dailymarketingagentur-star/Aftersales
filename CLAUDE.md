# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a German-language After-Sales platform for a marketing agency, consisting of three components:

1. **Business Documentation** — Process docs, email templates, checklists, and diagrams for an 11-phase after-sales process
2. **WordPress Plugin (client-operations-hub/)** — "Client Operations Hub" for WordPress Multisite (Paket 1 / MVP)
3. **Django SaaS (django/)** — Full SaaS platform with Django 5.x backend + Next.js 15 frontend (Increment 1)

## Language Convention

- **Documentation & file names:** German using **ae/oe/ue** instead of umlauts (ae for ä, oe for ö, ue for ü)
- **User-facing UI text** (frontend components, labels, messages): Uses **real German umlauts** (ä, ö, ü, Ä, Ö, Ü)
- Templates use `{{PLACEHOLDER}}` syntax (e.g. `{{KUNDENNAME}}`, `{{FIRMENNAME}}`). Documentation references Hormozi frameworks (4 R's, Value Equation, Anti-Churn Checklist).

## Django SaaS Commands (django/)

All commands run from the `django/` directory. Use `docker compose` directly (`make` is not available on this Windows system; a Makefile exists as reference for command equivalents).

```bash
# Container lifecycle
docker compose up -d --build           # Start all 6 Docker services
docker compose down                    # Stop and remove containers
docker compose down && docker compose up -d --build  # Restart all
docker compose logs -f                 # Follow all container logs
docker compose logs -f backend         # Follow backend logs only
docker compose logs -f frontend        # Follow frontend logs only

# Django management
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell_plus  # or shell as fallback

# Testing
docker compose exec backend pytest -x -v                 # All tests, stop on first failure
docker compose exec backend pytest --cov=apps --cov-report=html  # With coverage

# Linting
docker compose exec backend ruff check .                 # Ruff linter
docker compose exec backend ruff check --fix .           # Auto-fix
docker compose exec backend ruff format .                # Format
docker compose exec backend mypy .                       # Type checking

# Database & Redis
docker compose exec postgres psql -U aftersales -d aftersales
docker compose exec redis redis-cli FLUSHALL
```

Run a single test file or test function:

```bash
docker compose exec backend pytest apps/users/tests/test_views.py -x -v
docker compose exec backend pytest apps/users/tests/test_views.py::TestClassName::test_method -x -v
```

Management commands (seed data for fresh install):

```bash
docker compose exec backend python manage.py seed_service_types    # Service types (SEO, SEA, etc.)
docker compose exec backend python manage.py seed_email_templates  # 6 email templates
docker compose exec backend python manage.py seed_jira_templates   # Jira action templates
docker compose exec backend python manage.py seed_task_templates   # Task templates (11 phases)
```

Setup: copy `django/.env.example` to `django/.env` and `django/frontend/.env.example` to `django/frontend/.env`, then `docker compose up -d --build`. Migrations run automatically on container start via `entrypoint.sh`.

**URLs:** Backend API at localhost:8000, Frontend at localhost:3000, Django Admin at localhost:8000/admin/

### API Route Map

| Path | App |
|---|---|
| `/api/v1/auth/` | users — login, register, JWT, me, tenants |
| `/api/v1/tenants/` | tenants — CRUD |
| `/api/v1/members/` | users — member management |
| `/api/v1/billing/` | billing — Stripe checkout/portal |
| `/api/v1/audit/` | audit — event log |
| `/api/v1/emails/` | emails — templates, sequences |
| `/api/v1/clients/` | clients — client management |
| `/api/v1/service-types/` | clients — service type lookup |
| `/api/v1/integrations/` | integrations — 3rd-party connections (Jira, etc.) |
| `/api/v1/tasks/` | tasks — task management |
| `/health/` | health check (DB + Redis) |
| `/stripe/` | dj-stripe webhooks |

### Tenant-Exempt Paths (no X-Tenant-ID required)

`/admin/`, `/health/`, `/stripe/`, `/api/v1/auth/login/`, `/api/v1/auth/registration/`, `/api/v1/auth/token/refresh/`, `/api/v1/auth/password/reset/`, `/api/v1/auth/me/`, `/api/v1/auth/tenants/`, `/api/v1/tenants/`, `/__debug__/`, `/api/v1/emails/track/`, `/api/v1/integrations/twilio/twiml/`

All other paths require `X-Tenant-ID` header by default.

## Django Architecture

### Backend (django/backend/)

- **Settings:** `config/settings/{base,local,production,test}.py` — multi-environment via python-decouple
- **9 apps** in `apps/`: `common`, `tenants`, `users`, `billing`, `audit`, `emails`, `clients`, `integrations`, `tasks`
- **Multi-tenancy:** Tenant-per-row model. `TenantMiddleware` extracts `X-Tenant-ID` header → `request.tenant`. All data models inherit `TenantScopedModel` (abstract base with FK to Tenant). Postgres RLS via `EnableRLS` migration operation (`apps/common/db/rls.py`). `TenantAwareManager` provides `for_tenant()`/`for_tenant_id()` methods
- **Auth:** Email-based (no username), JWT in HTTP-only cookies (`access` / `refresh`) via dj-rest-auth + allauth + simplejwt. Access token: 15min, refresh: 7 days (rotation + blacklisting). Custom User model with UUID PK
- **Billing:** dj-stripe integration. `HasActiveSubscription` DRF permission raises 402 (`SubscriptionRequired` exception in `apps/common/exceptions.py`) if no active subscription. `TenantSubscription` caches Stripe status. Free tier: `is_active` returns True for `active`, `trialing`, or `free` status
- **Permissions** (`apps/common/permissions.py`): `IsTenantMember`, `IsTenantAdmin`, `IsTenantOwner`, `HasActiveSubscription`
- **API:** REST under `/api/v1/`, pagination 25 items, throttle 20/min (anon) / 100/min (user)
- **Async:** Celery + Redis for email delivery, scheduled tasks via celery-beat with DatabaseScheduler. Daily Jira health check at 07:00 hardcoded in `config/celery.py`
- **Encryption:** Fernet (from `cryptography` lib, derived from `DJANGO_SECRET_KEY` via PBKDF2) in `apps/common/encryption.py`. Used for email provider credentials, Jira/Twilio tokens
- **Audit:** Append-only `AuditEvent` with before/after JSON snapshots
- **Integrations registry:** `apps/integrations/registry.py` — 8 types (jira, hubspot, clickup, slack, activecampaign, agencyanalytics, calendly, twilio). Adding a new type only requires a registry entry
- **Testing:** pytest + factory-boy. Fixtures in `backend/conftest.py` (user_factory, tenant_factory, user, tenant, api_client, authenticated_client). Config in `pyproject.toml`. Test settings: Celery always-eager, throttling disabled, MD5 password hashing for speed
- **Linting:** ruff (line-length: 120, rules: E/F/W/I/N/UP/B/A/C4/SIM/TCH/RUF), mypy

### Frontend (django/frontend/)

- **Next.js 15** with App Router, React 19, TypeScript, Tailwind CSS, shadcn/ui
- **API proxy:** `next.config.ts` rewrites `/api/*` and `/stripe/*` to Django backend
- **Auth middleware:** `middleware.ts` checks JWT cookie, redirects unauthenticated to `/login`. Public paths: `/`, `/login`, `/register`, `/verify-email/*`
- **API client:** `src/lib/api.ts` — `apiFetch()` wrapper injects `X-Tenant-ID` header and credentials
- **Pages:** `(auth)/` for login/register/verify, `(dashboard)/` for protected routes, `(onboarding)/` for org creation
- **Dashboard routes:** `/dashboard/`, `/mandanten/` (clients), `/aufgaben/` (tasks, sub: `listen/`, `vorlagen/`), `/integrationen/` (sub: `email/`, `jira/`, `twilio/`), `/billing/`, `/cashflow/`, `/team/`, `/settings/`, `/optionen/`
- **Tenant state:** `TenantContext` stores current tenant ID in `localStorage` (`current_tenant_id`). `switchTenant()` calls `window.location.reload()`
- **shadcn/ui:** Style `new-york`, base color `neutral`. Add new components: `npx shadcn add <component>` inside frontend container
- **npm scripts:** `npm run dev` (turbopack), `npm run build`, `npm run lint` (eslint), `npm run format` (prettier)
- **Linting:** ESLint + Prettier with tailwind plugin

### Docker Services (6)

postgres:16, redis:7, backend (Python 3.12), celery, celery-beat, frontend (Node 22). Health checks on postgres and redis. Hot reload via volume mounts. Frontend uses `WATCHPACK_POLLING=true` for Windows file watching.

### Environment-Specific Settings

- **Local** (`local.py`): `CORS_ALLOW_ALL_ORIGINS = True`, `AUTH_PASSWORD_VALIDATORS = []`, debug_toolbar at `/__debug__/`, `InsecureSMTPBackend` (skips TLS verification)
- **Production** (`production.py`): Sentry (Django + Celery via `SENTRY_DSN`), gunicorn, Anymail/SendGrid, HSTS + SSL redirect + secure cookies, django-storages[s3] available
- **Email tracking:** `BACKEND_URL` env var required for open/click tracking pixel URLs in `EmailLog`

## WordPress Plugin Architecture (client-operations-hub/)

Pure PHP plugin (no build step, no Composer, no package manager). Requires WordPress 6.0+, PHP 8.0+.

- **Namespace:** `COH\` with SPL autoloader
- **Entry point:** `client-operations-hub.php` — loads autoloader, hooks activation/deactivation, initializes modules on `plugins_loaded`
- **8 custom DB tables** (prefix `coh_`): clients, task_templates, tasks, api_keys, api_key_audit, activity_log, reminders, health_history
- **REST API:** `wp-json/coh/v1/` with endpoints for dashboard, clients, tasks, API keys, webhooks. 5 custom capabilities for permission checks
- **Modules** (`includes/modules/`):
  - `Api_Vault` — AES-256-CBC encrypted API key storage + connection testing (HubSpot, ClickUp, Slack, ActiveCampaign, AgencyAnalytics, Calendly)
  - `Client_Intake` — Client CRUD, tier determination (Bronze/Silber/Gold/Platin by monthly volume), auto CRM integration
  - `Task_Engine` — Generates per-client tasks from 27 seeded templates across 11 phases. Day offsets from client start_date
  - `Dashboard` — Traffic-light signals (green/yellow/red) based on health score + overdue tasks
  - `Reminder` — WP Cron-based multi-channel reminders (email, admin notice, Slack). Hourly processing + daily overdue check at 08:00
- **Encryption:** `COH\Encryption` class, AES-256-CBC with random IVs, key from WP option or `COH_ENCRYPTION_KEY` constant
- **Admin UI:** jQuery AJAX against REST API, localized via `cohAdmin` JS object (restUrl, nonce, adminUrl)

## Documentation Structure

- `After-Sales-Prozess.md` — Master reference (7 parts, 11 phases, psychology + frameworks)
- `email-templates/` — 6 templates (Day 0 to Day 90), each with placeholders, A/B subject variants, and CRM action metadata
- `checklisten/` — Setup checklist (Phase 0) and welcome package specs with budget tiers
- `vorlagen/` — Onboarding questionnaire, kickoff agenda, NPS/testimonial framework, client health scorecard
- `diagramme/` — 6 Mermaid diagrams (flowchart, journey, gantt, stateDiagram, mindmap) with README index
- `Loesungsanalyse-After-Sales-Plattform.md` — Solution analysis comparing SaaS alternatives vs custom build

Files are numbered by phase/sequence (e.g. `01-willkommens-email.md` through `06-nps-review.md`). Documents include sign-off tables, cross-references, and operational metadata (timing, sender, CRM actions, follow-up automation).

## Post-Change Workflow

Regeln fuer Claude nach Code-Aenderungen im Docker-Stack:

- **Frontend-Aenderungen** (`.tsx`, `.ts`, Config-Dateien): Container-Logs kurz pruefen ob Turbopack re-compiled hat (`docker compose logs -f frontend`). Falls keine Recompilation sichtbar → `docker compose restart frontend`
- **Backend-Aenderungen** (`.py`): Django dev server reloaded automatisch via Volume-Mount. Bei Model-Aenderungen zusaetzlich: `docker compose exec backend python manage.py makemigrations && docker compose exec backend python manage.py migrate`
- **Neue npm/pip Dependencies**: `docker compose down && docker compose up -d --build` (Container-Rebuild noetig, da `node_modules`/pip packages im Image liegen)
- **Nach laengeren Aufgaben**: Kurze Verifikation dass Container laufen und Aenderungen sichtbar sind

## Kommunikation

- User ist Junior-Dev, Claude agiert als Senior-Dev
- Entscheidungen erklaeren (kurzes "warum")
- Bei nicht-trivialen Aenderungen: Was wurde gemacht und warum, in 2-3 Saetzen
- Proaktiv auf potentielle Probleme hinweisen

## Implementierungs-Prinzipien

### Einfach > Clever

Code der offensichtlich funktioniert ist besser als eleganter Code der subtil kaputt sein kann. Da Claude keinen Browser hat um Frontend-Aenderungen zu testen, gilt besonders:

- **Page-Reload statt State-Propagation:** Wenn `window.location.reload()` ein State-Problem zu 100% loest, ist das besser als eine React Context/useMemo/useCallback/useEffect-Chain die wahrscheinlich funktioniert
- **Keine useCallback/useMemo/useEffect-Chains ohne zwingenden Grund.** Jede Dependency-Array ist eine potentielle Fehlerquelle die erst zur Laufzeit sichtbar wird
- **Server-Redirect statt Client-Side-Router** wo moeglich
- **Bei UI-State-Bugs immer den Ansatz waehlen der am wenigsten von React-Laufzeitverhalten abhaengt**
- **Wenn die Wahl zwischen "clever aber unverifizierbar" und "simpel aber garantiert" besteht:** Explizit ansprechen und den simplen Ansatz empfehlen

### Integrations-Aufgaben (Tasks mit Aktionen)

Aufgaben die eine Integration-Aktion ausfuehren (E-Mail senden, Jira-Aktion, etc.) folgen einem festen Pattern:

- **Sichtbarer Aktions-Button** in der kompakten Task-Zeile (nicht nur im aufgeklappten Detail)
- **Klick oeffnet immer ein Modal** zur Bestaetigung/Vorschau der Aktion
- **Bei Erfolg:** Visuelles Feedback (gruener Text) + Aufgabe wird automatisch als erledigt markiert
- **Bei Fehler:** Sichtbare Fehlermeldung im Modal
- Bei neuen Integrations-Typen (z.B. Slack, ClickUp) dieses Pattern von Anfang an mitplanen
