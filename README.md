<div align="center">

# FastAPI · React Fullstack Template

**A ready-to-code development template: FastAPI backend, React frontend, PostgreSQL, Redis and Mailpit, all started with one command.**

[![CI](https://github.com/davidcastillocruz/FastAPI-React-Fullstack-Template/actions/workflows/ci.yml/badge.svg)](https://github.com/davidcastillocruz/FastAPI-React-Fullstack-Template/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

[Features](#features) · [Quick start](#quick-start) · [Project structure](#project-structure) · [Backend guide](#backend-guide) · [Frontend guide](#frontend-guide) · [Testing](#testing)

</div>

---

## Overview

The template comes with the plumbing every project ends up needing (configuration, logging, translated errors, languages, themes, rate limiting, emails, tests and CI) already built, reviewed and tested, plus one complete example feature to copy from.

The example is a small demo, **"Departures from localhost"**: you write an email address, React sends it to FastAPI, PostgreSQL saves it and a styled test email arrives at Mailpit. Every request shows up on a split-flap departures board.

> [!NOTE]
> This is a **development** template. There is no production setup on purpose (no production compose, no reverse proxy, no secrets management).

## Features

### Backend

- **Validated settings** with pydantic-settings: every variable is required, a missing or wrong value stops the app on startup, and validation errors never print secret values.
- **Async database** with SQLAlchemy 2 and asyncpg, a naming convention for constraints, and **Alembic** migrations applied automatically on startup.
- **Translated errors**: every error of the API answers `{"detail": "..."}` in the user's language (404, 405, 422, 429, 500 and your own), and the OpenAPI docs show the real shape.
- **Language system**: `?lang=` > `language` cookie > `Accept-Language` > default. Translation files are checked on startup (missing languages, different keys, wrong placeholders, repeated keys).
- **Structured logging**: one line per log with a request id and the client IP, extras as `key=value`, emails masked when sending, control characters escaped, colors in the terminal. Every response carries an `X-Request-ID` header.
- **Rate limiting** with slowapi, counters in Redis (with an in-memory fallback).
- **Background emails** with fastapi-mail, caught by Mailpit in development.
- **Tests** with pytest against a real PostgreSQL test database.

### Frontend

- **React 19 + Vite 8** in JavaScript, React Router and imports from `src` with the `@` alias.
- **Theme system**: light and dark themes as CSS variables. Follows the system live until the user picks one, saved in a cookie, applied before the first render.
- **Language system**: same languages and cookie as the backend, so the API always answers in the language of the page. `useT()` translates with named placeholders and checks every translation file in development.
- **Axios instance** with a timeout that sends the cookies, so the backend's errors arrive in the language of the page.
- **Component packages**: every page and component lives in its own folder with its JSX, CSS module and translations.
- **Tests** with Vitest, jsdom and Testing Library.

### Tooling

- **Docker Compose** for the whole stack, with hot reload in the backend and the frontend.
- **GitHub Actions**: backend tests, frontend lint, tests and build on every push.

## Tech stack

| Layer | Tools |
| --- | --- |
| Backend | Python 3.14, FastAPI, Pydantic, SQLAlchemy 2 (async), Alembic, slowapi, fastapi-mail |
| Frontend | React 19, Vite 8, React Router, axios, CSS modules, oxlint |
| Services | PostgreSQL 17, Redis 8, Mailpit |
| Testing | pytest, pytest-asyncio, httpx · Vitest, jsdom, Testing Library |
| Tooling | Docker Compose, GitHub Actions |

## Quick start

**Requirements:** [Docker](https://www.docker.com/) with Docker Compose. Node is only needed to run the frontend outside Docker.

```bash
git clone https://github.com/davidcastillocruz/FastAPI-React-Fullstack-Template.git
cd FastAPI-React-Fullstack-Template

cp backend/.env.api.example backend/.env.api
cp backend/.env.db.example backend/.env.db

docker compose up --build
```

Then open:

| Service | URL |
| --- | --- |
| Web | http://localhost:5173 |
| API docs (Swagger) | http://localhost:8000/docs |
| Mailpit (sent emails) | http://localhost:8025 |
| PostgreSQL (from a database client) | `localhost:5433` |

Saving a file reloads the API or the page. The migrations run every time the backend starts.

## Project structure

```
.
├── backend/
│   ├── src/
│   │   ├── main.py              # app, request logging middleware, CORS, routers
│   │   ├── core/                # settings, logger, languages, errors, limiter, email
│   │   ├── api/                 # dependencies (DbSession, Language) and one router per module
│   │   ├── modules/             # features: models, schemas, repositories, services, translations
│   │   ├── emails/              # email templates and their translations
│   │   ├── shared/schemas.py    # MessageResponse {message}, ErrorResponse {detail}
│   │   ├── database.py          # async engine, Base, get_db
│   │   └── models.py            # imports every model for SQLAlchemy and Alembic
│   ├── alembic/                 # migrations
│   └── tests/
├── frontend/
│   └── src/
│       ├── main.jsx             # providers and every route
│       ├── themes/              # theme variables, provider and useTheme
│       ├── languages/           # language provider, useLanguage and useT
│       ├── utils/               # api (axios) and cookies
│       ├── pages/               # one folder per page
│       ├── components/          # one folder per shared component
│       ├── hooks/               # shared hooks
│       └── features/            # big features with their own pages, components and hooks
├── .github/workflows/ci.yml
└── docker-compose.yml
```

## Backend guide

### Adding a module

Each feature is a module in `backend/src/modules/<module>/`, split in layers. Use `email_requests` as the reference.

1. **Model** in `models/`, then import it in `src/models.py` so Alembic sees it.
2. **Migration**: generate it, review the file in `alembic/versions/` and restart the backend to apply it.
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "create users"
   ```
3. **Schemas** in `schemas/`: what the endpoints receive and return.
4. **Repository** in `repositories/`: only database queries, no `try/except` (closing the session rolls back).
5. **Service** in `services/`: the logic. Catch only foreseeable errors and turn them into an `HTTPException`, the rest becomes a translated 500.
6. **Translations** in `translations/<module>_translations.json`.
7. **Router** in `src/api/routers/`, included in `main.py`.
8. **Tests** in `backend/tests/`.

### Errors and translations

Translation files hold every text in every language, with `%s` placeholders:

```json
{
  "USER_NOT_FOUND": {
    "en": { "detail": "User %s doesn't exist" },
    "es": { "detail": "El usuario %s no existe" }
  }
}
```

```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=get_error_detail("USER_NOT_FOUND", language, {"detail": (username,)}),
)
```

Successful responses that only carry a message use `MessageResponse` (`{"message": "..."}`), and every error answers `{"detail": "..."}`.

### Logging

```python
logger = logging.getLogger(__name__)
logger.info("User created", extra={"user_id": user.id})
```

The request id and the client IP are added to every line automatically. Keep the message fixed, put the data in `extra`, and never log personal data.

### Configuration

Every setting lives in `src/core/settings.py` and is **required**. A new setting goes in `Settings`, in your `.env` file and in its `.example`.

## Frontend guide

### Adding a page or a component

Every page and component is a folder with everything it needs:

```
pages/ProfilePage/
├── ProfilePage.jsx
├── ProfilePageStyle.module.css
└── ProfilePageTranslation.json
```

Pages are registered in `src/main.jsx`:

```jsx
const router = createBrowserRouter([
  { path: '/', element: <HomePage /> },
  { path: '/profile', element: <ProfilePage /> },
]);
```

### Translations

```json
{ "greeting": { "en": "Hello {name}", "es": "Hola {name}" } }
```

```jsx
const t = useT(translations);
t('greeting', { name: 'Ana' });
```

`const { language, setLanguage } = useLanguage()` reads or changes the language without reloading the page.

### Themes

The variables of `src/themes/themes.css` work in any CSS module without importing anything:

```css
.card {
  background: var(--color-surface);
  color: var(--color-text);
}
```

`const { theme, setTheme } = useTheme()` reads or changes the theme. A new variable goes in both themes.

### Calling the API

```js
import { api } from '@/utils/api';

try {
  const { data } = await api.post('/users', { email });
} catch (error) {
  // The backend's message, already translated. No response: the backend didn't answer
  setError(error.response?.data?.detail ?? t('noConnection'));
}
```

## Testing

```bash
docker compose exec backend pytest    # backend, against its own test database
cd frontend && npm test                # frontend
```

The backend tests create and use an `app_test` database in the same PostgreSQL, so your development data is never touched. `npx vitest` keeps the frontend tests running while you code.

### Continuous integration

On every push and pull request, GitHub Actions runs two jobs in parallel:

- **Backend**: pytest against a PostgreSQL 17 service.
- **Frontend**: oxlint, Vitest and the production build.

## Useful commands

| Task | Command |
| --- | --- |
| Start everything | `docker compose up --build` |
| Stop everything | `docker compose down` |
| Backend logs | `docker compose logs -f backend` |
| New migration | `docker compose exec backend alembic revision --autogenerate -m "..."` |
| Undo the last migration | `docker compose exec backend alembic downgrade -1` |
| Add a frontend dependency | `docker compose exec frontend npm install <package>` |
| Reinstall the frontend dependencies of the container | `docker compose up --build -V` |
| Lint the frontend | `cd frontend && npx oxlint src` |

---

<div align="center">

Made by [@davidcastillocruz](https://github.com/davidcastillocruz)

</div>
