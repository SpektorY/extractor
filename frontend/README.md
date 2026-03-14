# המחלץ — Frontend

React + TypeScript + Vite frontend for the Hamachletz (המחלץ) emergency management platform.  
Admin (war room) and volunteer mobile web.

## Requirements

- **Node.js 18+** (LTS recommended)
- **Backend** running at `http://localhost:8000` (or set `VITE_API_BASE_URL`)

## Quick start

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. (Optional) Configure environment

Create `.env` in the frontend directory if you need to override the API URL:

```bash
# Backend API base URL (default: http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Start the dev server

```bash
npm run dev
```

- App: http://localhost:5173  
- Admin login: http://localhost:5173/login  
- Volunteer flows use magic-link URLs from the backend.

## Scripts

| Command       | Description                    |
|---------------|--------------------------------|
| `npm run dev` | Start Vite dev server (HMR)    |
| `npm run build` | TypeScript check + production build |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint                     |

## Environment variables

| Variable             | Description              | Default              |
|----------------------|--------------------------|----------------------|
| VITE_API_BASE_URL    | Backend API base URL     | http://localhost:8000 |

Variables must be prefixed with `VITE_` to be exposed to the client.

## Stack

- **React 19** + **TypeScript**
- **Vite 7** — build and dev server
- **React Router 7** — routing
- **TanStack Query** — server state and caching
- **Tailwind CSS 4** — styling
- **shadcn/ui**-style components (CVA, clsx, tailwind-merge)

## Troubleshooting

- **CORS errors** — Ensure the backend has your frontend origin in `CORS_ORIGINS` (e.g. `http://localhost:5173`).
- **401 on API calls** — Log in at `/login`; the app sends the JWT in the `Authorization` header.
- **Backend not found** — Confirm the backend is running and `VITE_API_BASE_URL` points to it.
