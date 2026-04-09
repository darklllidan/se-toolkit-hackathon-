# Lab 10 — Task 2: Project Plan

## Project Idea

**End-user:** University students using shared campus facilities (dorms, study rooms, laundry areas).

**Problem:** Students have no way to know in advance whether a shared campus resource (washing machine, meeting room, rest area) is available — they show up and find it occupied, wasting time.

**One-sentence idea:** A web app that lets students browse and book shared campus resources in real time, eliminating wasted trips and scheduling conflicts.

**Core feature:** Resource booking with conflict prevention — a student can see available time slots for a resource and reserve one, with the system guaranteeing no double-bookings.

---

## Implementation Plan

### Version 1 — One core thing done well

**Feature:** Browse available resources and book a time slot from a convenient dashboard.

- Student logs in and lands on a dashboard showing all campus resources as cards (category, location, capacity, live availability status).
- Student clicks "Book" on any available resource, picks a date and time slot, confirms — booking is created instantly.
- The system prevents double-booking (enforced at the database level with a PostgreSQL GIST exclusion constraint).
- Student sees their active bookings in a dedicated "My Bookings" section on the same dashboard, with a cancel button on each.
- Dashboard updates in real time via WebSocket (no refresh needed).

| Layer    | Technology       |
|----------|------------------|
| Backend  | FastAPI (Python) |
| Database | PostgreSQL       |
| Client   | React + Vite     |
| Infra    | Docker Compose   |

This is a functioning product: a student can complete a full booking flow from the browser.

---

### Version 2 — Builds on Version 1

**Improvements:**
- Address TA feedback from the Version 1 review.
- Add an **AI assistant chat widget** (Claude API) embedded in the web app — students type natural language requests ("book a washing machine tomorrow at 10 am") and the assistant creates the booking.
- The assistant can also answer "what's available today?", cancel bookings, and show the user's upcoming reservations.
- Deploy the full stack to a university VM, accessible via Nginx reverse proxy.
- Add admin-facing resource management (create/disable resources) through the web app.

---

## Components

| Component                 | Role                                                                 |
|---------------------------|----------------------------------------------------------------------|
| **Backend** (FastAPI)     | Business logic, booking conflict enforcement, REST API, AI assistant endpoint |
| **Database** (PostgreSQL) | Persistent storage; prevents overlapping bookings at the DB level    |
| **Web app** (React + Vite)| Dashboard for browsing/booking resources + embedded AI chat widget   |
| **AI assistant** *(v2)*   | Claude-powered chat that books resources via natural language         |
