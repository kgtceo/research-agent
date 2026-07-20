# Deploy

Backend (FastAPI) → **Railway**; frontend (Next.js in `web/`) → **Vercel**. Push to
GitHub first.

## Backend → Railway
1. New Project → Deploy from GitHub repo → `research-agent`.
2. Railway uses the **`Dockerfile`** (installs deps, runs uvicorn on `$PORT`).
3. **Variables:** `ANTHROPIC_API_KEY`, `AGENT_CORS_ORIGINS` = your Vercel URL. (No
   search key needed — web search uses DuckDuckGo.)
4. Settings → **Networking → Generate Domain**. Set the domain's target port to the
   one in the deploy logs (`Uvicorn running on http://0.0.0.0:XXXX`).
5. `GET /health` → `{"ok":true,"configured":true}`.

## Frontend → Vercel
1. Add New → Project → import `research-agent`, **Root Directory = `web`**.
2. Env var `NEXT_PUBLIC_API_URL` = the Railway backend URL.
3. Deploy. Optionally attach `agent.kareemghazal.com` and add it to `AGENT_CORS_ORIGINS`.

Note: a research run makes several tool calls + model turns (~30–60s), which is why
the backend is a persistent service (Railway), not a serverless function.
