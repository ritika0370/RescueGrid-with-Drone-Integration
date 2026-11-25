# Disaster Response and Rescue Coordination Platform — Backend & AI Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.15-blue.svg?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?logo=postgresql)](https://postgresql.org)
[![Twilio](https://img.shields.io/badge/Twilio-Voice%20Hotline-F22F46.svg?logo=twilio)](https://twilio.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-15%2F15%20Passing-brightgreen.svg)]()

A modular, production-ready backend system for emergency and disaster response coordination. The platform bridges citizens reporting life-critical events, emergency departments coordinating logistics, drone pilots conducting aerial surveys, and AI engines analyzing multimodal disaster intelligence.

---

## Key Capabilities & Highlights

1. **Citizen Emergency SOS Ingestion (App, Web, Twilio Phone Calls)**:
   - Synchronous, zero-delay persistence and immediate acknowledgment (`SUBMITTED`).
   - Supports 9 standard emergency categories (Fire, Flood, Earthquake, Building collapse, Road accident, Medical emergency, Missing or trapped person, Industrial or chemical, Other).
   - Preserves all independent citizen reports, original descriptions, safety status, and individual GPS coordinates.
2. **Twilio Emergency Voice Hotline**:
   - Allows citizens without internet or mobile apps to report emergencies directly by calling a phone number.
   - Twilio TwiML interactive voice response (`<Gather input="speech">` and `<Record>`).
   - Automatically transcribes speech, extracts location and emergency category, creates an emergency report, groups it into the disaster incident, and feeds it into the live dispatch website dashboard in real-time.
3. **Multi-Factor Incident Grouping Engine**:
   - Evaluates spatial proximity (adaptive Haversine distance), temporal windows, category compatibility, NLP text token similarity (Jaccard), and landmark matching.
   - Calculates candidate match confidence:
     - **High Confidence ($\ge 0.70$)**: Auto-suggests/links to existing incident.
     - **Medium Confidence ($0.35 - 0.69$)**: Queues candidate link for officer review.
     - **Low Confidence ($< 0.35$)**: Generates a new independent provisional incident.
   - Supports officer review actions: **Confirm**, **Reject**, **Merge**, and **Split**.
4. **Multimodal AI Emergency Analysis Engine**:
   - **Text**: Urgency indicators, extracted locations, trapped and injured person counts, structural and environmental hazard detection.
   - **Audio**: Speech-to-text with uncertainty tracking and language preservation.
   - **Images**: Object detection (floodwater, fire, smoke, structural damage, vehicles, human sightings) with bounding boxes and confidence scores.
   - **Safety Guardrail**: Never claims a person is trapped merely because an image detects a human silhouette. Distinguishes confirmed citizen statements from AI detections.
5. **Transparent Priority Assessment (P1 - P4)**:
   - Evaluates immediate threat to life, trapped count, injured count, category severity, and time elapsed.
   - Full human override support with recorded justification and immutable audit logging.
6. **Department Routing & Notifications**:
   - Matches category capabilities and geographic service areas to specialized rescue departments (Fire, Police, Disaster Response, Medical).
   - WebSocket real-time event broadcasting to department channels.
7. **Drone Station Registry & Mission Job Cards**:
   - Recommends optimal available drones based on proximity, battery $>50\%$, and flight range.
   - Generates structured Survey Job Cards with target coordinates, survey boundary polygon, known trapped locations, and department instructions.
8. **Manual Pilot Operation Workflow**:
   - Complete state machine: `ASSIGNED` $\rightarrow$ `ACCEPTED` / `REJECTED` $\rightarrow$ `PREPARING` $\rightarrow$ `IN_FLIGHT` $\rightarrow$ `COMPLETED`.
   - Pilot submits verified field observations with coordinates, photos, hazard markers, and navigation corridor notes.
   - Survey AI synthesizes aerial findings, updating situation reports.
9. **Final Rescue Intelligence Report (JSON & Downloadable PDF)**:
   - Compiles all 9 mandated sections: Incident Identification, Executive Summary, Citizen Reports, Geographic Information, Drone Survey Findings, AI Analysis, Suggested Rescue Planning, Evidence and Audit Trail, and Operational Disclaimer.
   - Built-in PDF generator produces standardized, downloadable `.pdf` reports without external browser binaries.

---

## System Architecture

```
                                  [ CITIZEN ACTORS ]
                         /                  |                  \
              Mobile SOS App          Web Portal         Twilio Phone Call
             (React Native)          (React/Next.js)      (+1-800-HOTLINE)
                     \                      |                      /
                      \                     |                     /
  ==================== \ ================== | ================== / ====================
                        REST API (/api/v1) & Twilio Webhooks
  ====================================================================================
                                            |
                                  [ FastAPI Backend ]
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
 [ Ingestion Engine ]             [ Multi-Factor Grouping ]           [ AI Analysis Pipeline ]
 - Immediate Acknowledge           - Spatial Proximity (Haversine)    - Text Urgency & Trapped NLP
 - SHA-256 Media Hashing           - Temporal Window                  - Audio STT with Uncertainty
 - Thumbnail Generation            - Category Compatibility           - Vision Hazards & Detection
 - Untrusted Input Guard           - Jaccard Text Similarity          - Citations & Confidence
         |                                  |                                  |
         +----------------------------------+----------------------------------+
                                            |
                              [ Database & Storage Layer ]
                               PostgreSQL (SQLAlchemy 2.0)
                               Local Object Store (Uploads)
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
 [ Department Routing ]          [ Drone Fleet & Missions ]       [ Final Intelligence Report ]
 - Category Capabilities          - Station Telemetry Fleet        - 9 Mandated Sections
 - Geographic Service Boundary    - Job Card Polygon Generator     - Structured JSON
 - WebSocket Live Events          - Manual Pilot State Machine     - Downloadable PDF (1.4)
                                  - Field Observation Logger       - Non-repudiation Audit Trail
```

---

## Twilio Voice Hotline Integration

When a citizen dials the configured Twilio hotline:

```
[ Citizen Dials Phone ]
           │
           ▼
[ Twilio Requests: POST /api/v1/twilio/voice/incoming ]
           │
           ├─ Returns TwiML: <Say> "Disaster Response Hotline..." </Say>
           │                 <Gather input="speech" action="/process-speech">
           │                 <Record action="/recording-callback">
           ▼
[ Citizen Speaks Emergency & Location ]
           │
           ▼
[ Twilio Webhook: POST /api/v1/twilio/voice/process-speech ]
           │
           ├─ 1. Parses speech result & caller phone number
           ├─ 2. Classifies emergency category (Flood, Fire, etc.)
           ├─ 3. Ingests as Citizen Report (source="TWILIO_VOICE")
           ├─ 4. Feeds directly into real-time dispatch website dashboard (WebSocket)
           ├─ 5. Evaluates Grouping Engine & links to disaster incident
           └─ 6. Returns TwiML: <Say> "Report received and fed into dispatch..." </Say>
```

### Twilio Configuration (`.env`)
As requested, credentials remain safe placeholders ready to be filled:
```env
TWILIO_ACCOUNT_SID="AC_TWILIO_PLACEHOLDER_ACCOUNT_SID"
TWILIO_AUTH_TOKEN="TWILIO_PLACEHOLDER_AUTH_TOKEN"
TWILIO_PHONE_NUMBER="+18005550199"
TWILIO_WEBHOOK_BASE_URL="http://your-ngrok-or-domain.com"
```

---

## Project Structure

```
disaster-response-platform/
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration revisions
│   ├── env.py                    # Alembic environment configuration
│   └── script.py.mako
├── app/
│   ├── adapters/                 # Pluggable hardware & AI adapters
│   │   ├── base_stt.py           # Abstract Base Class for Speech-to-Text
│   │   ├── base_vision.py        # Abstract Base Class for Computer Vision
│   │   ├── mock_stt.py           # Deterministic STT provider with uncertainty
│   │   ├── simulated_vision.py   # Deterministic disaster object detection
│   │   ├── storage_adapter.py    # SHA-256 validation, storage, and thumbnails
│   │   ├── whisper_stt.py        # OpenAI Whisper adapter
│   │   └── yolo_vision.py        # Ultralytics YOLOv8 adapter
│   ├── api/                      # REST & WebSocket route definitions
│   │   ├── deps.py               # Authentication & RBAC dependencies
│   │   └── v1/
│   │       ├── ai.py             # Multimodal analysis endpoints
│   │       ├── auth.py           # User registration, login, refresh, profile
│   │       ├── departments.py    # Department registry & incident queues
│   │       ├── drones.py         # Drone fleet & telemetry endpoints
│   │       ├── final_reports.py  # 9-section report JSON & PDF export
│   │       ├── incidents.py      # Incident review, merge, and split
│   │       ├── missions.py       # Job cards & manual pilot workflow
│   │       ├── reports.py        # Citizen SOS ingestion & media upload
│   │       ├── twilio_webhook.py # Twilio phone call ingestion & callbacks
│   │       └── websockets.py     # Live room subscriptions
│   ├── core/
│   │   ├── config.py             # Pydantic Settings & environment variables
│   │   ├── database.py           # Async SQLAlchemy 2.0 engine & sessions
│   │   ├── events.py             # WebSocket ConnectionManager
│   │   └── security.py           # RFC 7519 JWT & PBKDF2-HMAC password hashing
│   ├── models/                   # SQLAlchemy relational database models
│   │   ├── ai_analysis.py        # Multimodal findings & citations
│   │   ├── audit_log.py          # Operational decision audit trail
│   │   ├── department.py         # Emergency departments & capabilities
│   │   ├── drone.py              # Stations, drones, and telemetry
│   │   ├── incident.py           # Grouped incidents & report links
│   │   ├── media.py              # Media files, SHA-256 hashes, transcripts
│   │   ├── mission.py            # Job cards & survey states
│   │   ├── notification.py       # Outbound notifications
│   │   ├── observation.py        # Pilot & sensor field sightings
│   │   ├── report.py             # Independent citizen reports
│   │   ├── twilio_call.py        # Inbound phone call logs
│   │   └── user.py               # Users with RBAC roles
│   ├── schemas/                  # Pydantic request and response schemas
│   │   ├── ai.py
│   │   ├── auth.py
│   │   ├── department.py
│   │   ├── drone.py
│   │   ├── incident.py
│   │   ├── mission.py
│   │   ├── observation.py
│   │   ├── report.py
│   │   ├── rescue_report.py
│   │   └── twilio.py
│   ├── services/                 # Business logic & domain services
│   │   ├── ai_service.py         # NLP extraction & combined synthesis
│   │   ├── audit_service.py      # Decision trail logger
│   │   ├── drone_service.py      # Drone registration & telemetry updates
│   │   ├── grouping_service.py   # Multi-factor incident grouping engine
│   │   ├── media_service.py      # Media ingestion & pipeline coordinator
│   │   ├── mission_service.py    # Job card generation & drone selection
│   │   ├── pdf_service.py        # Standard-compliant PDF 1.4 report writer
│   │   ├── pilot_service.py      # Manual pilot survey operations
│   │   ├── priority_service.py   # Explainable P1-P4 priority assessment
│   │   ├── report_service.py     # SOS report ingestion
│   │   ├── rescue_report_service.py # 9-section report compiler
│   │   ├── routing_service.py    # Department matching & notification
│   │   └── twilio_service.py     # Twilio voice call emergency processor
│   └── main.py                   # FastAPI application initialization
├── scripts/
│   ├── seed_demo.py              # Populates users, departments, and drones
│   └── simulate_workflow.py      # Complete end-to-end disaster scenario simulation
├── tests/                        # Automated Pytest suite (15 tests)
│   ├── conftest.py
│   ├── test_ai_analysis.py
│   ├── test_auth.py
│   ├── test_drone_missions.py
│   ├── test_grouping.py
│   ├── test_reports.py
│   ├── test_rescue_report.py
│   └── test_twilio.py
├── uploads/                      # Local object storage
│   ├── media/
│   ├── reports_pdf/
│   └── thumbnails/
├── .env.example                  # Environment configuration template
├── docker-compose.yml            # FastAPI + PostgreSQL + Redis deployment
├── Dockerfile                    # Multi-stage production container
└── requirements.txt              # Python dependencies
```

---

## Installation & Quickstart

### Option 1: Local Development Setup

1. **Navigate to the platform directory**:
   ```powershell
   cd C:\Users\RAJIT\.gemini\antigravity\scratch\disaster-response-platform
   ```

2. **Configure Environment Variables**:
   ```powershell
   Copy-Item .env.example .env
   ```

3. **Run Seed Data Script**:
   Initializes default users (Officer, Pilot, Admin, Citizens), departments, and drones:
   ```powershell
   python scripts/seed_demo.py
   ```

4. **Start the FastAPI Backend**:
   ```powershell
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Access Interactive Swagger Documentation**:
   Open browser at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option 2: Docker Compose Deployment

Run the complete multi-service stack (FastAPI Backend, PostgreSQL 16, and Redis 7):

```bash
docker-compose up --build -d
```

- API Base: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432` (db: `disaster_db`, user: `postgres`)
- Redis: `localhost:6379`

---

## Running Automated Tests

Run the full test suite with `pytest`:

```powershell
python -m pytest tests --rootdir=. -o cache_dir=.pytest_cache -v
```

All 15 unit and integration tests validate:
- Authentication & RFC 7519 JWT verification
- SOS report ingestion with immediate acknowledgment
- SHA-256 cryptographic media hashing
- Multi-factor incident grouping & officer merge/split
- NLP extraction and explainable P1-P4 priority assessment
- Drone Job card generation and manual pilot lifecycle
- 9-section Rescue Intelligence Report JSON & binary PDF export
- Twilio phone hotline TwiML generation and speech processing into reports

---

## End-to-End Demonstration Scenario

To execute the realistic Section 19 flood disaster workflow:

```powershell
python scripts/simulate_workflow.py
```

This script:
1. Ingests 4 independent citizen SOS reports (water entering home, stranded vehicles, trapped persons on balcony, flooded road photo).
2. Simulates an incoming Twilio voice emergency phone call from a citizen without an app.
3. Groups the reports into a unified Flood incident while preserving all 5 independent records and GPS locations.
4. Assesses priority as **P1 (Critical)** and routes assignment to Regional Disaster & Flood Response Agency.
5. Generates a drone survey job card with boundary coordinates and hazard markers.
6. Executes manual pilot workflow: accepts job card, conducts flight, logs human sightings and clear water navigation corridors, and marks survey completed.
7. Synthesizes drone observations using post-survey AI.
8. Compiles the official 9-section Rescue Intelligence Report and exports a downloadable PDF.

---

## Default Demo Credentials

| Role | Name | Email | Password |
|---|---|---|---|
| **Admin** | Admin Commander | `admin@disaster.org` | `Password123!` |
| **Officer** | Officer John Commander | `officer.john@disaster.org` | `Password123!` |
| **Pilot** | Pilot Sarah Sky | `pilot.sarah@rescue.org` | `Password123!` |
| **Citizen** | Citizen Alice | `alice@citizen.org` | `Password123!` |
| **Citizen** | Citizen Bob | `bob@citizen.org` | `Password123!` |
