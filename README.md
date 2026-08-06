# ResQMesh — AI Disaster Relief Coordination Platform

Government command portal + FastAPI backend for coordinating disaster relief: shelters, hospitals, resources, SOS reports, and AI flood prediction.

---

## Prerequisites

Install these on the new machine before starting:

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.12+ | https://www.python.org/downloads/ |
| **Node.js** | 18+ (20 LTS recommended) | https://nodejs.org/ |
| **npm** | Comes with Node.js | — |
| **Git** | Any recent version | https://git-scm.com/ |

Optional: **Docker Desktop** if you prefer running the backend in a container.

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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### What the seed script does

- Creates SQLite tables (`disaster_relief.db`)
- Inserts demo users, hospitals, shelters, disasters, **resources**, reports, notifications

Re-run safely anytime (skips existing records):

```bash
python -m app.database.seed
```

Reset everything and re-seed:

```bash
python -m app.database.seed --reset
```

### Backend URLs

| URL | Purpose |
|-----|---------|
| http://localhost:8000/health | Health check |
| http://localhost:8000/docs | Swagger API docs |
| http://localhost:8000/api/v1 | REST API base |

### Environment file (`backend/.env`)

Copy from `.env.example`. Important variables:

```env
DATABASE_URL=sqlite:///./disaster_relief.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000
SECRET_KEY=change-this-secret-key-before-deploying
```

If the frontend runs on another machine, add that machine’s origin to `CORS_ORIGINS`, e.g.:

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

Open **http://localhost:5173**

### Frontend environment (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

**Running frontend on a different device than the backend?**  
Set `VITE_API_BASE_URL` to the backend machine’s LAN IP:

```env
VITE_API_BASE_URL=http://192.168.1.100:8000/api/v1
```

Also add the frontend URL to `CORS_ORIGINS` in `backend/.env`.

Restart `npm run dev` after changing `.env`.

### Production build (optional)

```bash
npm run build
npm run preview
```

---

## 4. Default login (auto-used by the portal)

The UI logs in automatically on first API call:

| Field | Value |
|-------|-------|
| Email | `gov.admin@tn.gov.in` |
| Password | `ResQMesh@2024!` |

Other seeded accounts (same password):

| Role | Email |
|------|-------|
| NGO | `priya@redcross.in` |
| Volunteer | `vikram.volunteer@gmail.com` |
| Hospital | `meera@apollochennai.in` |
| Citizen | `ramesh.citizen@gmail.com` |

---

## 5. Project structure

```
ResQMesh-main/
├── backend/          FastAPI + SQLite + ML
│   ├── app/          API routes, services, models
│   ├── ml/           Flood prediction model training
│   └── requirements.txt
├── frontend/         React + Vite + Tailwind
│   └── src/
│       ├── pages/    Dashboard, Resources, Shelters, etc.
│       └── lib/api.ts
└── README.md
```

---

## 6. Portal pages

| Route | Feature |
|-------|---------|
| `/` | Command dashboard (KPIs, charts) |
| `/prediction` | AI flood risk analysis |
| `/resources` | Resource inventory & registration |
| `/shelters` | Shelter capacity & check-in/out |
| `/hospitals` | Hospital bed management |
| `/reports` | Citizen SOS report verification |
| `/settings` | Portal preferences (local UI) |

---

## 7. AI prediction (optional)

Flood prediction needs a trained model file. If you get a 503 on the Prediction page:

```bash
cd backend
.\.venv\Scripts\Activate.ps1   # or source .venv/bin/activate
python ml/train_sensor_model.py
```

Then restart the backend.

---

## 8. Troubleshooting

### White / blank screen after 1 second

- Usually a JavaScript crash when API data loads.
- Open browser DevTools → **Console** for the error.
- Ensure the **backend is running** and seeded.
- Hard refresh: `Ctrl+F5` (Windows) / `Cmd+Shift+R` (Mac).

### “Error loading resource pools” / Resource Allocation not working

Common causes:

1. **Backend not running** — start `uvicorn` in `backend/`.
2. **Database not seeded** — run `python -m app.database.seed`.
3. **CORS blocked** — add your frontend URL to `CORS_ORIGINS` in `backend/.env`.
4. **Wrong API URL** — set `VITE_API_BASE_URL` in `frontend/.env` to match the backend host.

The Resource Allocation page previously crashed because the UI expected `latitude`, `longitude`, and `unit` fields that the backend does not store. That is fixed — the page now matches the real API shape.

### Register New Inventory fails

- Resource types must match backend allowed values: `food_packet`, `drinking_water`, `rescue_boat`, `medical_kit`, `generator`, `medicine`, `blankets`, `fuel`, etc.
- You must be logged in as a **Government** user (the portal does this automatically).

### API calls fail / 401 Unauthorized

- Clear browser storage: DevTools → Application → Local Storage → delete `resqmesh_token`.
- Reload the page so auto-login runs again.

### Port already in use

```powershell
# Find process on port 8000 (Windows)
netstat -ano | findstr :8000

# Find process on port 5173
netstat -ano | findstr :5173
```

---

## 9. Quick start checklist (new device)

- [ ] Python 3.12+ and Node.js 18+ installed  
- [ ] `backend`: venv created, `pip install -r requirements.txt`  
- [ ] `backend`: `.env` copied from `.env.example`  
- [ ] `backend`: `python -m app.database.seed`  
- [ ] `backend`: `uvicorn app.main:app --reload` → http://localhost:8000/health OK  
- [ ] `frontend`: `npm install`  
- [ ] `frontend`: `.env` with correct `VITE_API_BASE_URL`  
- [ ] `frontend`: `npm run dev` → http://localhost:5173 loads  
- [ ] Dashboard shows data; Resource Allocation lists seeded supplies  

---

## 10. Tech stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLite, Alembic, scikit-learn  
**Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, TanStack Query, Recharts, Framer Motion

---

## License / credits

ResQMesh Coordination Portal — disaster relief coordination demo platform.
