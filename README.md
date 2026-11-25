# RescueGrid AI — Disaster Response & Rescue Coordination Platform

AI-powered disaster SOS, incident intelligence, drone-assisted reconnaissance and rescue coordination platform.

**End-to-end workflow (live):**

Citizen SOS → Report ID → Intelligent incident grouping → AI analysis & priority → Department routing → Officer review → Drone mission job card → Manual pilot survey → Survey AI analysis → Final rescue intelligence report (JSON + PDF)

---

## Architecture

```
RescueGrid-AI/
├── apps/
│   └── web-dashboard/     # Next.js command dashboard + citizen web + Expo mobile
├── backend/               # FastAPI + SQLAlchemy + AI services
├── scripts/               # Startup, seed
├── docs/
├── demo/
├── storage/
├── shared/
├── .env.example
└── README.md
```

### Interfaces

1. **Citizen SOS** — Web (`/citizen`) and Expo mobile (`apps/web-dashboard/mobile`)
2. **Command Dashboard** — Emergency department / officer UI
3. **Pilot workspace** — Mission accept, survey, observations

All share the same backend (`/api/v1`) and database.

---

## Technology Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI, SQLAlchemy 2 (async), Pydantic v2, Alembic |
| Database | SQLite (demo) / PostgreSQL 16 (production) |
| Auth | JWT (access + refresh), RBAC (admin, officer, pilot, citizen) |
| AI | Simulated vision + configurable STT; optional YOLO / Whisper |
| Frontend | Next.js 16, React 19, Tailwind, Leaflet / OSM |
| Mobile | Expo (React Native) |
| Realtime | WebSocket event channel |
| Media | Local filesystem (`uploads/`) |

---

## Prerequisites

- Python 3.11+
- Node.js 18+ and pnpm (or npm)
- Optional: Docker for PostgreSQL, Expo CLI for mobile device

---

## Quick Start (Local, SQLite)

### 1. Backend

```bash
cd RescueGrid-AI/backend
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install greenlet   # required for SQLAlchemy asyncio
cp .env.example .env
# Default DATABASE_URL is SQLite — no Postgres needed for demo

python3 scripts/seed_demo.py

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

### 2. Command Dashboard + Citizen Web

```bash
cd RescueGrid-AI/apps/web-dashboard
# Ensure .env.local has:
#   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
#   NEXT_PUBLIC_DEMO_MODE=false

pnpm install   # or npm install
pnpm dev       # or npm run dev → http://localhost:3000
```

- Dashboard / login: http://localhost:3000  
- Citizen SOS: http://localhost:3000/citizen  

### 3. Mobile (Expo)

```bash
cd RescueGrid-AI/apps/web-dashboard/mobile
# Set EXPO_PUBLIC_API_BASE_URL to your LAN IP (not localhost), e.g. http://192.168.1.10:8000
npx expo start
```

---

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@disaster.org | Password123! |
| Officer | officer.john@disaster.org | Password123! |
| Pilot | pilot.sarah@disaster.org | Password123! |

---

## Demo Scenario

1. Seed: `python3 scripts/seed_demo.py`
2. Submit 3–4 flood SOS reports with nearby GPS (citizen UI or curl).
3. Backend groups them into one incident (Haversine + category + text Jaccard).
4. AI suggests priority (P1–P4).
5. Officer login → review incident → create mission → assign drone/pilot.
6. Pilot accepts → submit observations → complete.
7. Final rescue intelligence report (JSON + PDF in `uploads/reports_pdf/`).

Full pipeline simulation:

```bash
cd backend && python3 scripts/simulate_workflow.py
```

---

## Key API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/v1/auth/login | JWT login |
| POST | /api/v1/reports | Citizen SOS (immediate ack) |
| GET | /api/v1/reports/my | My reports |
| GET | /api/v1/incidents | List incidents |
| PATCH | /api/v1/incidents/{id} | Priority/status override |
| POST | /api/v1/missions | Create drone job card |
| POST | /api/v1/missions/{id}/accept | Pilot accept |
| POST | /api/v1/missions/{id}/observations | Survey findings |
| GET | /api/v1/drones | Fleet |
| GET | /api/v1/departments | Departments |
| WS | /api/v1/ws/events | Realtime |

OpenAPI: http://localhost:8000/docs

---

## Environment

See `.env.example` and `backend/.env.example`.

- CORS open for local dev.
- Media served from `/uploads/...`
- AI: `VISION_PROVIDER=simulated` (no heavy model download).
- Twilio optional (voice hotline).

---

## Docker (Postgres + API)

```bash
cd backend
docker compose up --build
docker compose exec api python scripts/seed_demo.py
```

---

## Testing

```bash
cd backend
pytest tests/ -q
```

Integration checks performed:

- Backend health & login
- SOS → REPORT_ID
- Multi-report spatial grouping → single INCIDENT
- Priority suggestion
- Seeded users, departments, drones

---

## Known Limitations

- Vision/STT use simulated adapters unless external keys/models configured.
- Drone telemetry simulated; flight control is external/manual.
- Demo departments only — no real government system integration.
- Physical mobile devices need LAN IP, not localhost.

---

## Security

- Change `SECRET_KEY` before non-demo use.
- Do not commit real API keys.
- RBAC enforced on officer/pilot endpoints.

