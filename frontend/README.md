# ResQMesh Frontend

React + TypeScript command portal for the ResQMesh disaster relief
coordination platform. See the [root README](../README.md) for what the
platform does overall and how to run the full stack — this file covers the
frontend specifically.

**Stack:** React 19 · TypeScript · Vite · Tailwind CSS v4 · TanStack Query · Recharts · Framer Motion · axios · react-router-dom

---

## Pages

| Route | Component | What it does |
|---|---|---|
| `/` | `Dashboard.tsx` | Live KPIs, severity/shelter/hospital charts, external situational feed (weather + earthquakes). Polls every 20s. |
| `/prediction` | `AIPrediction.tsx` | Two tabs: Flood Risk (8-input sensor form) and Resource Priority (18-input incident form, AI-predicted priority + relief units). |
| `/resources` | `ResourceAllocation.tsx` | Inventory CRUD plus a "Suggested Allocations" panel with one-click apply. |
| `/shelters` | `Shelters.tsx` | Capacity tracking with check-in/check-out. |
| `/hospitals` | `Hospitals.tsx` | Bed/ICU/equipment capacity management. |
| `/reports` | `Reports.tsx` | Citizen SOS report verification and disaster linking. |
| `/priority` | `PriorityRanking.tsx` | Two tabs: computed severity-of-need ranking, and urgency+accessibility ranking. |
| `/coordination` | `Coordination.tsx` | Cross-org assignment board — create, filter, and transition volunteer/NGO/hospital/resource assignments. |
| `/settings` | `Settings.tsx` | Local UI preferences only, no backend calls. |

## Project structure

```
frontend/
├── src/
│   ├── pages/            One file per route, listed above
│   ├── components/
│   │   ├── Layout.tsx      Page shell — sidebar + navbar + <Outlet />
│   │   ├── Sidebar.tsx     Nav links
│   │   ├── Navbar.tsx      Top bar
│   │   └── ErrorBoundary.tsx  Catches render errors app-wide
│   ├── lib/api.ts         Axios instance, auth, response envelope helpers (see below)
│   ├── App.tsx            Routes
│   └── main.tsx           Entry point
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.*.json
└── .oxlintrc.json
```

## The API client (`src/lib/api.ts`)

Everything talks to the backend through one shared axios instance:

- **Auto-login**: the portal logs in as the seeded government admin
  (`gov.admin@tn.gov.in`) automatically on first API call, via a request
  interceptor. The JWT is cached in `localStorage` (`resqmesh_token`) so
  subsequent loads skip the login round-trip. Concurrent requests share one
  in-flight login promise rather than each firing their own `/auth/login`
  call.
- **Response envelope helpers**: the backend wraps every response as
  `{ success, message, data, errors }` (and adds `pagination` for list
  endpoints). `unwrapEnvelope()`, `unwrapList()`, and `unwrapDashboardHospitals()`
  pull the useful part out so pages don't repeat that logic.
- **`formatApiError()`**: turns FastAPI validation error payloads (which can
  be a string, or an array of `{msg, loc}` objects) into a plain string safe
  to render directly — pages that skip this and render the raw error object
  will crash with "Objects are not valid as a React child."
- **401 handling**: a response interceptor clears the cached token on 401 so
  the next request re-triggers auto-login.

## State & data fetching

TanStack Query for all server state — no separate global store. Pages that
share data (e.g. Dashboard and Shelters both list shelters) use the same
query key so they share one cache entry instead of double-fetching.
`refetchInterval` is set on the Dashboard and Priority Ranking queries for
live polling; everything else fetches on mount/mutation only.

## Setup / running

```bash
npm install
cp .env.example .env      # sets VITE_API_BASE_URL
npm run dev                # http://localhost:5173
```

Requires the backend running on port 8000 (see `../backend/README.md`) —
the frontend has nothing to render without it.

```bash
npm run build      # production build to dist/
npm run preview     # serve the production build locally
npm run lint         # oxlint
```

## Known limitations

- TypeScript `strict` mode is not enabled — combined with some `err: any`
  catch blocks, null-safety issues aren't caught at compile time (several
  bugs fixed during development were exactly this class of issue).
- The production bundle is a single ~940KB chunk, not code-split.
- The portal only ever authenticates as the government role — there's no UI
  for logging in as NGO/Volunteer/Hospital/Citizen, even though the backend
  supports all five roles.
