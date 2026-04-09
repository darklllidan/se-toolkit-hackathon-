# Campus resource booking (SE Toolkit Lab 10)

Web app for browsing and booking shared campus resources (rooms, laundry, etc.) with conflict-safe scheduling, FastAPI backend, React frontend, Telegram bot hooks, and Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Optional: Node.js / Python for local development outside containers

## Quick start

1. Clone the repository and enter the project directory.

2. Copy the environment template and fill in values (generate strong secrets for production):

   ```bash
   cp .env.example .env
   ```

3. Start the stack:

   ```bash
   docker compose up --build
   ```

4. Open the app (see `docker-compose.yml` / nginx config for ports; typically HTTP on port 80 when using the default nginx setup).

`docker-compose.override.yml` enables dev-friendly settings (e.g. exposed DB/backend ports, backend hot reload). Remove or adjust it for production-style deployments.

## Repository layout

| Path | Role |
|------|------|
| `backend/` | FastAPI app, Alembic migrations |
| `frontend/` | React + Vite client |
| `bot/` | Telegram bot service |
| `nginx/` | Reverse proxy configuration |

## Push to GitHub

1. Create an empty repository on GitHub (no README/license if you already have them locally).

2. Add the remote and push:

   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git branch -M main   # optional: rename default branch
   git push -u origin main
   ```

3. Confirm `.env` is **not** listed in the repo on GitHub. If secrets were ever committed, remove them from history and rotate all exposed credentials.
