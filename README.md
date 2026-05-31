# Deadlock Pulse API

**Live match watcher as a backend service** — not another todo app.

Python + FastAPI + SQL + JWT + background polling + signed webhooks.  
Built as a backend version of the same integration idea from [Undeadlocked](../DeadlockSniper): watch Steam IDs via [Deadlock API](https://api.deadlock-api.com), persist events, notify external systems.

## Why this stands out in a portfolio

| Typical Junior project | Deadlock Pulse |
|---|---|
| CRUD todo list | Real third-party API integration |
| No auth | JWT (OAuth2 password flow) |
| In-memory data | SQLAlchemy + SQLite (PostgreSQL-ready) |
| No background jobs | Async poller every 45s |
| No webhooks | HMAC-signed outbound webhooks |
| Only ORM | Raw SQL analytics endpoint |

## Stack

- **FastAPI** — REST API + OpenAPI docs
- **SQLAlchemy 2.0** — async ORM
- **SQLite** — zero setup (swap to PostgreSQL via `DATABASE_URL`)
- **JWT** — `python-jose`
- **httpx** — async HTTP to Deadlock API
- **Background task** — asyncio poller on startup

## Quick start (local)

```powershell
cd C:\Users\1\Documents\deadlock-pulse-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open:

- Dashboard: http://127.0.0.1:8000/
- Swagger: http://127.0.0.1:8000/docs

## Quick start (Docker + PostgreSQL)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```powershell
cd C:\Users\1\Documents\deadlock-pulse-api
docker compose up --build
```

Or double-click `docker.bat`.

- API: http://127.0.0.1:8000/
- PostgreSQL: `localhost:5432` (user/pass/db: `pulse` / `pulse` / `deadlock_pulse`)

Optional Deadlock API key:

```powershell
$env:DEADLOCK_API_KEY="your-key"
docker compose up --build
```

## CI (GitHub Actions)

On push/PR, workflow runs:

1. **test** — pytest against PostgreSQL service (auth, watches, raw SQL analytics)
2. **docker** — build image + `docker compose up` smoke test (`/health`, `/status`)

Badge for README after pushing to GitHub:

```markdown
![CI](https://github.com/YOUR_USER/deadlock-pulse-api/actions/workflows/ci.yml/badge.svg)
```

## Demo flow

1. **Register** → `POST /auth/register` with email + password
2. **Login** → `POST /auth/login` → copy `access_token`
3. **Add watch** → `POST /watches` with Steam ID64
4. Poller checks Deadlock API every 45s
5. When player enters a new match → row in `match_events` + webhook fired
6. **Analytics** → `GET /analytics/heroes` (raw SQL GROUP BY)

### Test webhooks

Use [webhook.site](https://webhook.site) — copy your unique URL:

```http
POST /webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://webhook.site/your-id",
  "secret": "my-signing-secret"
}
```

Payload includes `X-Pulse-Signature` header (HMAC-SHA256).

## API overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create user |
| POST | `/auth/login` | Get JWT |
| GET/POST/DELETE | `/watches` | Watch list |
| GET | `/events` | Match history |
| GET/POST/DELETE | `/webhooks` | Outbound hooks |
| GET | `/status` | Service metrics |
| GET | `/analytics/heroes` | Raw SQL stats |

## Project structure

```
deadlock-pulse-api/
├── app/                    # FastAPI application
├── tests/                  # pytest (PostgreSQL in CI)
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml      # API + PostgreSQL
├── requirements.txt
└── requirements-dev.txt
```

```
app/
├── main.py              # FastAPI app + lifespan
├── models.py            # SQL tables
├── database.py          # Async SQLAlchemy
├── routers/             # HTTP endpoints
├── services/
│   ├── deadlock_client.py   # External API
│   ├── poller.py            # Background job
│   └── webhook_dispatcher.py
└── auth/                # JWT + passwords
```

## Interview pitch (30 sec)

> «Я перенёс свой опыт интеграции с Deadlock API из C# desktop-tool в production-style Python backend: JWT, SQL, фоновый poller и signed webhooks. Это не учебный CRUD — сервис реально опрашивает внешний API и хранит историю событий.»

## PostgreSQL

Docker Compose уже поднимает PostgreSQL. Для локального запуска без Docker:

```env
DATABASE_URL=postgresql+asyncpg://pulse:pulse@localhost:5432/deadlock_pulse
```

`asyncpg` уже в `requirements.txt`.

## AI workflow note

Project scaffolded with Cursor: architecture first (models → services → routers), then AI-generated code reviewed and trimmed for production patterns (async session, HMAC webhooks, raw SQL analytics).
