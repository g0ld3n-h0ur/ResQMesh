# ResQMesh — Disaster Relief Coordination Platform

ResQMesh is a command portal for coordinating disaster relief operations: tracking shelters, hospitals, and resource inventory; verifying citizen SOS reports; running AI flood-risk predictions; and — its core feature — **computing where limited relief resources should go first**, using explainable scoring rather than manual guesswork.

It's a full-stack demo/hackathon-stage project: a FastAPI + SQLite backend and a React + TypeScript frontend.

## What it actually does

- **Coordination CRUD** — disasters, shelters, hospitals, resource inventory, and citizen emergency (SOS) reports, all role-gated (Government / NGO / Volunteer / Hospital / Citizen).
- **AI flood prediction** — a trained RandomForest model estimates flood probability from rainfall, river level, soil moisture, and five other sensor inputs.
- **Need scoring** — every active disaster gets a computed 0–100 need score, blending assessed severity, citizen report volume, resource shortfall, and response lifecycle urgency. Updates as the situation changes — it isn't just the manually-set severity field.
- **Urgency + accessibility ranking** — disasters are also ranked by combining need with real distance (haversine) to the nearest shelter and hospital, surfacing which urgent situations are actually reachable right now.
- **Resource allocation optimization** — unassigned resource stock is automatically split across active disasters proportional to need (largest-remainder apportionment), so nothing sits idle and higher-need disasters get a fairer share. Suggestions are reviewed and applied by a human, never auto-committed.
- **Live dashboard** — polls every 20 seconds so coordinators see an evolving situation without manually refreshing.

---

## Tech stack

| Layer | Stack |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, SQLite, Alembic, scikit-learn, JWT auth |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, TanStack Query, Recharts, Framer Motion |

---

## Prerequisites

Install these on the new machine before starting:

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.12+ | https://www.python.org/downloads/ |
| **Node.js** | 18+ (20 LTS recommended) | https://nodejs.org/ |
| **npm** | comes with Node.js | — |
| **Git** | any recent version | https://git-scm.com/ |

Optional: **Docker Desktop**, if you'd rather run the backend in a container.

---

## 1. Get the project

```bash
git clone <your-repo-url>
cd ResQMesh-main
```

Or copy/unzip the project folder onto the new device.

---

## 2. Backend setup (API — port 8000)

Open a terminal in the `backend` folder.

### Windows (PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m app.database.seed
python ml/train_sensor_model.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### macOS / Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.database.seed
python ml/train_sensor_model.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **Don't skip `ml/train_sensor_model.py`.** The trained model file isn't committed to git (it's a 30+ MB binary artifact), so the AI Prediction page will return `503` on a fresh clone until you train it locally. It only takes a few seconds and only needs to be run once.

Confirm it's up: open **http://localhost:8000/health** — you should see `{"status":"healthy"}`.

### What the seed script does

- Creates SQLite tables (`disaster_relief.db`)
- Inserts demo users, hospitals, shelters, disasters, resources, reports, and notifications
- Safe to re-run anytime — it skips records that already exist:

```bash
python -m app.database.seed
```

- Reset everything and re-seed from scratch:

```bash
python -m app.database.seed --reset
```

### Backend URLs

| URL | Purpose |
|-----|---------|
| http://localhost:8000/health | Health check |
| http://localhost:8000/docs | Interactive Swagger API docs |
| http://localhost:8000/api/v1 | REST API base |

### Environment file (`backend/.env`)

Copied from `.env.example`. The variables that actually matter for local dev:

```env
DATABASE_URL=sqlite:///./disaster_relief.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000
SECRET_KEY=change-this-secret-key-before-deploying
```

The default `SECRET_KEY` is fine for local/demo use, but the backend will log a startup warning if you leave it unchanged — generate a real one before deploying anywhere reachable by others:

```bash
python -c "import secrets; print(secrets.token_hex(64))"
```

If the frontend runs on another machine, add that machine's origin to `CORS_ORIGINS`, e.g.:

```env
CORS_ORIGINS=http://localhost:5173,http://192.168.1.50:5173
```

### Docker (optional)

```bash
cd backend
docker compose up --build
```

---

## 3. Frontend setup (UI — port 5173)

Open a **second** terminal in the `frontend` folder.

```bash
cd frontend
npm install
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
npm run dev
```

Open **http://localhost:5173**.

### Frontend environment (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

**Running frontend and backend on different devices?** Point the frontend at the backend machine's LAN IP:

```env
VITE_API_BASE_URL=http://192.168.1.100:8000/api/v1
```

...and add the frontend's origin to `CORS_ORIGINS` in `backend/.env` (see above). Restart `npm run dev` after changing `.env`.

### Production build (optional)

```bash
npm run build
npm run preview
```

---

## 4. Logging in

The UI logs in automatically on first API call — no action needed:

| Field | Value |
|-------|-------|
| Email | `gov.admin@tn.gov.in` |
| Password | `ResQMesh@2024!` |

This account's password stays fixed across reseeds so auto-login keeps working. The other four seeded accounts (NGO, Volunteer, Hospital, Citizen) get a fresh **random** password every time you run the seed script — printed once to the backend console when it runs. You only need those if you're testing role-specific API access directly (e.g. via `/docs`); the portal itself only ever logs in as government.

| Role | Email |
|------|-------|
| NGO | `priya@redcross.in` |
| Volunteer | `vikram.volunteer@gmail.com` |
| Hospital | `meera@apollochennai.in` |
| Citizen | `ramesh.citizen@gmail.com` |

---

## 5. Portal pages

| Route | Feature |
|-------|---------|
| `/` | Command dashboard — live KPIs and charts, auto-refreshes every 20s |
| `/prediction` | AI flood risk analysis |
| `/resources` | Resource inventory, registration, and **suggested allocations** |
| `/shelters` | Shelter capacity & check-in/out |
| `/hospitals` | Hospital bed management |
| `/reports` | Citizen SOS report verification |
| `/priority` | Computed disaster ranking — severity of need, and urgency + accessibility |
| `/settings` | Portal preferences (local UI only, no backend) |

---

## 6. A few API endpoints worth knowing about

Full interactive reference is at `/docs`, but these are the ones behind the "smart" features:

| Endpoint | What it returns |
|---|---|
| `GET /api/v1/disasters/need-scores` | Active disasters ranked by computed need (severity + reports + resource shortfall + lifecycle stage), with a full component breakdown |
| `GET /api/v1/disasters/distribution-priority` | The same, blended with real distance to the nearest shelter/hospital |
| `GET /api/v1/resources/allocation-suggestions` | Suggested (resource → disaster, quantity) allocations for all unassigned stock, proportional to need |
| `PATCH /api/v1/resources/{id}/allocate` | Applies an allocation — the endpoint the "Apply" button in the UI actually calls |

---

## 7. Project structure

```
ResQMesh-main/
├── backend/
│   ├── app/              API routes, services, models, schemas
│   ├── ml/                Flood prediction model (train_sensor_model.py, predict.py)
│   ├── alembic/            Database migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/          Dashboard, Resources, Shelters, Priority Ranking, etc.
│       ├── components/     Layout, Sidebar, Navbar, ErrorBoundary
│       └── lib/api.ts       Axios client, auth, response helpers
└── README.md
```

---

## 8. Troubleshooting

### AI Prediction page returns 503
The flood model hasn't been trained locally yet (it's not committed to git). Run:
```bash
cd backend
python ml/train_sensor_model.py
```
Then restart the backend.

### White / blank screen after loading
Open browser DevTools → Console for the actual error. Usually means the backend isn't running or isn't seeded — check `/health` and re-run the seed script.

### "Error loading resource pools" / Resource Allocation not working
1. Backend not running — start `uvicorn` in `backend/`.
2. Database not seeded — run `python -m app.database.seed`.
3. CORS blocked — add your frontend's origin to `CORS_ORIGINS` in `backend/.env`.
4. Wrong API URL — check `VITE_API_BASE_URL` in `frontend/.env` matches the backend host.

### Register New Inventory fails
Resource types must match backend allowed values: `food_packet`, `drinking_water`, `rescue_boat`, `medical_kit`, `generator`, `medicine`, `blankets`, `fuel`, etc. You must be logged in as a Government user (the portal does this automatically).

### 429 Too Many Requests on login
The backend rate-limits `/auth/login` (10/min) and `/reports/emergency` (5/min) per IP as basic abuse protection. Wait a minute and retry — this is expected behavior, not a bug.

### API calls fail / 401 Unauthorized
Clear browser storage: DevTools → Application → Local Storage → delete `resqmesh_token`, then reload so auto-login runs again.

### Port already in use
```powershell
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :5173
```
```bash
# macOS / Linux
lsof -i :8000
lsof -i :5173
```

---

## 9. Quick start checklist (new device)

- [ ] Python 3.12+ and Node.js 18+ installed
- [ ] `backend`: venv created, `pip install -r requirements.txt`
- [ ] `backend`: `.env` copied from `.env.example`
- [ ] `backend`: `python -m app.database.seed`
- [ ] `backend`: `python ml/train_sensor_model.py` (required — model isn't in git)
- [ ] `backend`: `uvicorn app.main:app --reload` → http://localhost:8000/health returns OK
- [ ] `frontend`: `npm install`
- [ ] `frontend`: `.env` with correct `VITE_API_BASE_URL`
- [ ] `frontend`: `npm run dev` → http://localhost:5173 loads
- [ ] Dashboard shows live data; Resource Allocation lists seeded supplies and suggested allocations; Priority Ranking shows ranked disasters

---

## License / credits

ResQMesh Coordination Portal — disaster relief coordination demo platform.
