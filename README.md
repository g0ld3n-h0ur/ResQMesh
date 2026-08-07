# ResQMesh — Disaster Relief Coordination Platform

ResQMesh is a command portal for coordinating disaster relief operations. It's built for a government-led response team, with NGOs, hospitals, and volunteers plugged into the same system — tracking shelters, hospitals, and resource inventory; verifying citizen SOS reports; and — its core feature — **computing where limited relief resources should go first**, using explainable scoring and two trained ML models rather than manual guesswork.

It's a full-stack demo/hackathon-stage project: a FastAPI + SQLite backend and a React + TypeScript frontend.

---

## The problem this solves

During a disaster, relief organizations have to decide, over and over, with incomplete information: *which of these ten affected areas do we help first, and with what?* Normally that's manual — someone reads through reports, eyeballs a map, and makes a judgment call. Decisions get delayed, resources go to whoever asked loudest rather than whoever needs it most, and nobody has a live picture of what's actually happening on the ground beyond what's been typed into the system.

ResQMesh's job is to close that gap: pull in real signals (citizen reports, resource stock, live weather, live earthquake data), turn them into a ranked, explainable answer to "where first," and give every organization type — not just the government coordinator — a shared, live view of who's doing what.

---

## How it works

Everything below is real and running — not a mockup. Here's the mechanism behind each piece:

**Severity / need scoring.** Every active disaster gets a 0–100 need score, recomputed live, from four weighted signals: the government-assessed severity level, how many citizen SOS reports have come in for it, how depleted its already-assigned resources are, and how far along its response lifecycle is (a disaster that's just been reported and has nothing allocated yet scores higher than one that's already being handled). This is not the same number as the manual severity dropdown — it's a second, continuously-updated opinion derived from actual activity in the system. `backend/app/services/need_score_service.py`.

**Urgency + accessibility ranking.** A second ranking blends that need score (60% weight) with real accessibility (40%) — the straight-line distance from the disaster to the nearest registered shelter and hospital, computed with the haversine great-circle formula. Two equally urgent disasters get split by which one responders can actually reach right now. `backend/app/services/priority_service.py`.

**Resource allocation optimization.** When relief stock is sitting unassigned in a depot, the system runs a largest-remainder (Hamilton) apportionment: it weights every active disaster by its need score and splits the stock proportionally, guaranteeing every unit is accounted for and higher-need disasters get a fairer share — without a human doing the math. It only *suggests* — a coordinator reviews and clicks Apply, which calls the same manual allocation endpoint. `backend/app/services/allocation_service.py`.

**External data consolidation.** The backend makes live calls to two independent, free, keyless public APIs — Open-Meteo for current weather at each active disaster's coordinates, and the USGS Earthquake Hazards Program for recent significant earthquakes worldwide — and merges the results with internal disaster records into one feed on the dashboard. This is real third-party data fetched on every request, not seeded or faked. `backend/app/services/external_data_service.py`.

**AI-predicted allocation priority & relief units.** Two scikit-learn models — a RandomForestClassifier and a RandomForestRegressor — were trained on 200,000 real incident records from a hackathon-provided dataset (`disaster_relief_resource_allocation.csv`). Given 18 incident details (population affected, infrastructure damage, accessibility, resource stock on hand, funding available, etc.), they predict a priority label (Low/Medium/High/Critical, with per-class confidence) and a recommended relief-unit count. Test-set accuracy: 75% / 0.72 macro F1 for priority, R²=0.94 for relief units — both measured on 40,000 rows the models never trained on. `backend/ml/train_priority_model.py`, `backend/ml/predict.py`.

**AI flood risk prediction.** A separate RandomForest model estimates flood probability from 8 environmental sensor readings (rainfall, river level, soil moisture, temperature, humidity, prior flood history, elevation, population density). `backend/ml/train_sensor_model.py`.

**Cross-org coordination.** An assignment system links volunteers, NGOs, hospitals, and resources to a specific disaster, each with its own status lifecycle (pending → in progress → completed/cancelled, with role-appropriate permissions on who can transition what). Every organization type shows up in one shared board rather than siloed views. `backend/app/services/assignment_service.py`, `/coordination` page.

**Live dashboard.** Polls every 20 seconds so a coordinator watching the dashboard sees an evolving situation — new reports, changing resource levels, updated rankings — without hitting refresh.

---

## What it actually does (quick reference)

- **Coordination CRUD** — disasters, shelters, hospitals, resource inventory, and citizen emergency (SOS) reports, all role-gated (Government / NGO / Volunteer / Hospital / Citizen).
- **AI flood prediction** — see above.
- **Need scoring** — see above.
- **Urgency + accessibility ranking** — see above.
- **Resource allocation optimization** — see above.
- **Live dashboard** with a live external situational feed.
- **External data consolidation** — see above.
- **AI-predicted allocation priority & relief units** — see above.
- **Cross-org coordination** — see above.

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
| **Python** | **exactly 3.12.x** — see warning below | https://www.python.org/downloads/ |
| **Node.js** | 18+ (20 LTS recommended) | https://nodejs.org/ |
| **npm** | comes with Node.js | — |
| **Git** | any recent version | https://git-scm.com/ |

Optional: **Docker Desktop**, if you'd rather run the backend in a container.

> ⚠️ **Use Python 3.12, not whatever is newest.** `scikit-learn==1.5.2` (pinned
> in `requirements.txt`) has no prebuilt wheel for Python 3.13/3.14 yet, so
> `pip install` will try to compile it from source and fail with a confusing
> `meson`/compiler error unless you have a C compiler installed. This has
> nothing to do with your code — it's purely a missing-wheel problem.
>
> **Check what `python` resolves to before creating the venv:**
> ```bash
> python --version
> ```
> If that's not 3.12.x and you have multiple Python versions installed, target
> 3.12 explicitly instead of the generic `python -m venv .venv` below:
> ```powershell
> # Windows, using the py launcher
> py -3.12 -m venv .venv
> ```
> ```bash
> # macOS / Linux, if python3.12 is on PATH
> python3.12 -m venv .venv
> ```

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

> **Don't skip `ml/train_sensor_model.py`.** The trained model file isn't committed to git (it's a 30+ MB binary artifact), so the Flood Risk tab will return `503` on a fresh clone until you train it locally. It only takes a few seconds and only needs to be run once.

Confirm it's up: open **http://localhost:8000/health** — you should see `{"status":"healthy"}`.

### Optional: the Resource Priority model

The **Resource Priority** tab (`/prediction`) needs its own trained models, separate from the flood model above. Unlike the flood model, this one requires the real hackathon-provided dataset, which also isn't committed to git (67 MB):

```bash
# 1. Copy the dataset the hackathon host provided into place:
cp disaster_relief_resource_allocation.csv backend/ml/datasets/

# 2. Train both models (~30s on 200k rows):
cd backend
python ml/train_priority_model.py
```

This prints real accuracy/F1 and MAE/R² metrics and writes
`ml/models/priority_classifier.pkl` and `relief_units_regressor.pkl`. Skip this
if you don't have the dataset — every other feature works fine without it, the
Resource Priority tab will just 503 until it's trained.

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
| `/coordination` | Cross-org assignment board — create and track volunteer/NGO/hospital/resource assignments |
| `/settings` | Portal preferences (local UI only, no backend) |

The Dashboard (`/`) also shows the live external situational feed (weather + earthquakes), and `/prediction` has two tabs — Flood Risk and Resource Priority (the hackathon-dataset-trained models).

---

## 6. A few API endpoints worth knowing about

Full interactive reference is at `/docs`, but these are the ones behind the "smart" features:

| Endpoint | What it returns |
|---|---|
| `GET /api/v1/disasters/need-scores` | Active disasters ranked by computed need (severity + reports + resource shortfall + lifecycle stage), with a full component breakdown |
| `GET /api/v1/disasters/distribution-priority` | The same, blended with real distance to the nearest shelter/hospital |
| `GET /api/v1/resources/allocation-suggestions` | Suggested (resource → disaster, quantity) allocations for all unassigned stock, proportional to need |
| `PATCH /api/v1/resources/{id}/allocate` | Applies an allocation — the endpoint the "Apply" button in the UI actually calls |
| `GET /api/v1/external-data/situational-feed` | Live weather (per active disaster) + recent earthquakes, merged with internal data |
| `POST /api/v1/prediction/predict-priority` | AI-predicted allocation priority + recommended relief units (see below) |
| `GET /api/v1/assignments/` | List/filter cross-org assignments; `POST`/`PATCH .../status` to create and transition them |

---

## 7. Project structure

```
ResQMesh-main/
├── backend/
│   ├── app/              API routes, services, models, schemas
│   ├── ml/                Flood + resource-priority models (train_sensor_model.py, train_priority_model.py, predict.py)
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

### `pip install -r requirements.txt` fails with a `meson`/compiler error mentioning scikit-learn
Your `python` is newer than 3.12 (most likely 3.13 or 3.14) and there's no
prebuilt scikit-learn wheel for it yet, so pip tries to compile from source
and fails without a C compiler. Fix: delete the `.venv` you just created and
recreate it targeting Python 3.12 specifically — see the Prerequisites
warning above (`py -3.12 -m venv .venv` on Windows, `python3.12 -m venv .venv`
on macOS/Linux). Verified working end-to-end on 3.12; verified failing on 3.14.

### AI Prediction page returns 503
Neither trained model is committed to git — train the one you need:
```bash
cd backend
python ml/train_sensor_model.py      # Flood Risk tab
python ml/train_priority_model.py    # Resource Priority tab (needs the dataset — see above)
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
