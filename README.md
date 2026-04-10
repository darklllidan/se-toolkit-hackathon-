# Campus Resource Sync

One-line description: a web application for browsing and booking shared campus resources in real time, with conflict-safe scheduling, live updates, and an embedded AI assistant.

## Demo

Screenshots of the student dashboard (timeline view) and the booking flow:

| Timeline & resources | Booking dialog |
|----------------------|----------------|
| ![Dashboard — timeline view](docs/screenshots/dashboard-timeline.png) | ![Booking flow](docs/screenshots/booking-modal.png) |

## Product context

### End users

- **Primary:** university students who use shared campus facilities (dorms, laundry rooms, study rooms, meeting rooms, rest areas).
- **Secondary:** campus administrators (TA/admin accounts) who monitor resources and bookings.

### Problem that your product solves for end users

Students often walk to a washing machine, study room, or meeting room only to find it already in use. There is no reliable, shared view of **who booked what and when**, so time is wasted and small conflicts arise around shared spaces.

### Your solution

**Campus Resource Sync** gives students a single place to see resources, pick a free time slot, and book it. The backend enforces **no overlapping bookings** at the database level. The dashboard stays fresh with **WebSocket** updates, and an **AI assistant** helps with natural-language questions and actions (e.g. checking availability or booking through chat).

## Features

### Implemented

- Student **registration** and **login** (JWT access/refresh).
- **Dashboard** with a **timeline** of resources and **“My Bookings”** with cancel.
- **Booking** with time-slot selection; **double-booking prevented** by PostgreSQL constraints.
- **Live** connection indicator; updates pushed over **WebSockets**.
- **AI assistant** panel (OpenRouter) for conversational help and booking-related actions.
- **Admin** login, resource list, toggling resources between **available** and **maintenance**, and viewing/cancelling **all bookings**.
- **Docker Compose** stack: PostgreSQL, migrations, FastAPI, React build, Nginx reverse proxy.

### Not yet implemented / out of scope for the default stack

- **Telegram bot** code exists under `bot/`, but it is **not** included in the root `docker-compose.yml`; running it requires a separate process or Compose service (bot token, secrets).
- **Creating new resource records** from the UI (seed/migrations supply initial resources; admins can enable/disable and manage bookings).
- **HTTPS / Let’s Encrypt** in-repo (deployment steps below assume HTTP on port 80; TLS can be added in front of Nginx).
- **Email / push notifications** for reminders (not part of the default Compose file).

## Usage

1. **Open the app** in a browser at the URL where the stack is served (by default **`http://<server-ip>`** on port **80**, or `http://localhost` when testing on the VM itself).
2. **Register** as a student (name, building, room, password) or use an existing account.
3. On the **Timeline** tab, pick a resource and a free slot, then **confirm** the booking.
4. Switch to **My Bookings** to see upcoming reservations and **cancel** if needed.
5. Use the **AI assistant** widget for questions or guided actions (requires a valid `OPENROUTER_API_KEY` in `.env`).
6. **Admins** sign in via the admin login route in the app and use the admin dashboard to manage resource status and bookings.

API documentation is available at **`/api/docs`** (Swagger) when the backend is exposed accordingly (through Nginx: **`/api/docs`**).

## Deployment

Target environment: **Ubuntu 24.04 LTS** (same family as typical university lab VMs).

### What should be installed on the VM

- **Git** — clone the repository.
- **Docker Engine** and the **Docker Compose plugin** — run the stack in containers.
- **Open firewall port 80** (and **443** if you add HTTPS later) so users can reach Nginx.

Optional but useful: `curl`, `ufw` (firewall), `htop`.

### Step-by-step deployment instructions

1. **Update the system and install Git**

   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y git
   ```

2. **Install Docker** (official convenience script from Docker, or follow [Docker’s Ubuntu guide](https://docs.docker.com/engine/install/ubuntu/))

   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker "$USER"
   ```

   Log out and back in so the `docker` group applies (or use `newgrp docker`).

3. **Allow HTTP** (adjust if you use another firewall tool)

   ```bash
   sudo ufw allow OpenSSH
   sudo ufw allow 80/tcp
   sudo ufw enable
   ```

4. **Clone the product repository**

   ```bash
   git clone https://github.com/YOUR_ORG_OR_USER/YOUR_REPO.git
   cd YOUR_REPO
   ```

5. **Configure environment**

   ```bash
   cp .env.example .env
   nano .env   # or vim
   ```

   Set at least:

   - `POSTGRES_*` — strong database password.
   - `SECRET_KEY`, `BOT_INTERNAL_SECRET` — long random strings (e.g. `openssl rand -hex 32`).
   - `OPENROUTER_API_KEY` — if you use the AI assistant.
   - `FRONTEND_URL` — **public origin** of the web app as users open it (e.g. `http://YOUR_VM_IP` or your domain). This must match the browser origin for CORS.

   Never commit `.env` to Git.

6. **Build and start the stack**

   ```bash
   docker compose up -d --build
   ```

   Wait until `migrate` completes and `backend`, `frontend`, `nginx`, and `db` are running (`docker compose ps`).

7. **Verify**

   - From your laptop: open `http://YOUR_VM_IP` (or your DNS name).
   - Optional: `curl -sSf http://YOUR_VM_IP/api/docs | head` to confirm the API is proxied.

8. **Updates after code changes**

   ```bash
   cd YOUR_REPO
   git pull
   docker compose up -d --build
   ```

`docker-compose.override.yml` is intended for **local development** (extra ports, backend reload). On a production VM you can **remove or not copy** that file so only `docker-compose.yml` is used.

---

**Repository layout:** `backend/` (FastAPI), `frontend/` (React + Vite), `nginx/` (reverse proxy), `bot/` (optional Telegram bot, not started by default Compose).
