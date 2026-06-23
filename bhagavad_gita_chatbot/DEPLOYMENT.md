# ☁️ Deployment Guide — Render

This guide covers deploying the **Bhagavad Gita AI Counselor** as two separate
Render Web Services from a single GitHub repository using the included
`render.yaml` Blueprint.

---

## Architecture on Render

```
GitHub Repository
       │
       ▼ (render.yaml Blueprint)
┌─────────────────────────────────────────────────────┐
│                   Render Platform                    │
│                                                      │
│  Service 1: gita-counselor-backend                   │
│  ┌─────────────────────────────────────────────┐    │
│  │  FastAPI + Uvicorn                           │    │
│  │  • /chat  • /search_verse                   │    │
│  │  • /verse_of_the_day  • /chapter_summary     │    │
│  │  Env: GEMINI_API_KEY, CHROMA_DB_PATH         │    │
│  └─────────────────────────────────────────────┘    │
│                        ▲                             │
│                        │ HTTP (BACKEND_URL)           │
│  Service 2: gita-counselor-frontend                  │
│  ┌─────────────────────────────────────────────┐    │
│  │  Streamlit                                   │    │
│  │  Env: BACKEND_URL                            │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

> **Deployment order matters:** Deploy the **backend first**, then set its
> public URL as `BACKEND_URL` in the frontend service.

---

## Prerequisites

- A [Render account](https://render.com) (free tier is sufficient)
- Your code pushed to a **public or private GitHub repository**
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

---

## Step 1 — Push to GitHub

```bash
# Initialize (if not already a git repo)
git init
git add .
git commit -m "Initial commit"

# Create a repo on GitHub, then:
git remote add origin https://github.com/<your-username>/<your-repo>.git
git branch -M main
git push -u origin main
```

> **Before pushing**, confirm `.env` is in `.gitignore` and `GEMINI_API_KEY`
> is NOT in any committed file. Run `git status` and check.

---

## Step 2 — Deploy via Blueprint (Recommended)

The `render.yaml` file defines both services. Render reads it automatically.

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New → Blueprint**
3. Connect your GitHub account and select your repository
4. Render detects `render.yaml` and shows a preview of both services
5. Click **Apply** — both services begin building

> The Blueprint creates both services but you must set secret environment
> variables manually (Step 3 + Step 4). Render never reads `sync: false`
> values from the file.

---

## Step 3 — Set Backend Environment Variables

After the blueprint is applied:

1. Go to **Dashboard → gita-counselor-backend → Environment**
2. Add the following environment variables:

| Key | Value | Notes |
|---|---|---|
| `GEMINI_API_KEY` | `AIza...your_key` | **Required.** Get from [AI Studio](https://aistudio.google.com/app/apikey) |
| `CHROMA_DB_PATH` | `./data/chromadb` | Already set in render.yaml |
| `PYTHONUNBUFFERED` | `1` | Already set in render.yaml |

3. Click **Save Changes** — the backend restarts automatically

> **Free tier note:** ChromaDB data is stored on an **ephemeral filesystem**
> on the free plan. The vector store rebuilds automatically on each deploy
> (~2–3 min on cold start). For persistent storage, upgrade to the
> **Starter plan** ($7/mo) and uncomment the `disk:` block in `render.yaml`.

---

## Step 4 — Set Frontend Environment Variables

1. Wait for the backend to finish deploying (status: **Live**)
2. Copy the backend's public URL from the Render dashboard. It looks like:
   ```
   https://gita-counselor-backend.onrender.com
   ```
3. Go to **Dashboard → gita-counselor-frontend → Environment**
4. Add:

| Key | Value |
|---|---|
| `BACKEND_URL` | `https://gita-counselor-backend.onrender.com` |

5. Click **Save Changes** — the frontend restarts

---

## Step 5 — Verify Deployment

### Backend health check
```
GET https://gita-counselor-backend.onrender.com/status
```
Expected response:
```json
{"configured": true}
```

### Frontend
Open:
```
https://gita-counselor-frontend.onrender.com
```
You should see the Bhagavad Gita AI Counselor UI load within a few seconds.

> **Cold start:** Free-tier Render services spin down after 15 minutes of
> inactivity. The first request after a cold start takes ~30–60 seconds.
> This is expected — subsequent requests are fast.

---

## Manual Deployment (Without Blueprint)

If you prefer to create services manually in the Render dashboard:

### Backend Service
| Setting | Value |
|---|---|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 1` |
| **Health Check Path** | `/status` |

### Frontend Service
| Setting | Value |
|---|---|
| **Runtime** | Python 3 |
| **Build Command** | `pip install streamlit requests python-dotenv` |
| **Start Command** | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` |
| **Health Check Path** | `/_stcore/health` |

---

## Updating the Deployment

Every `git push` to your `main` branch automatically triggers a new build
on Render (auto-deploy is enabled by default).

```bash
git add .
git commit -m "feat: improve response formatting"
git push origin main
```

Both services rebuild in parallel.

---

## Environment Variable Reference

| Variable | Service | Required | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Backend | ✅ Yes | Google Gemini API key |
| `CHROMA_DB_PATH` | Backend | No | Path to ChromaDB store (default: `./data/chromadb`) |
| `HOST` | Backend | No | Bind host (Render sets via `$PORT`) |
| `PYTHONUNBUFFERED` | Both | No | Disables Python output buffering |
| `BACKEND_URL` | Frontend | ✅ Yes | Full public URL of the backend service |

---

## Troubleshooting

### "Unable to connect to the backend" in the UI
- Verify `BACKEND_URL` in the frontend service environment is the **exact**
  Render URL of the backend (no trailing slash).
- Check the backend service logs in the Render dashboard for startup errors.

### Backend returns `{"configured": false}`
- `GEMINI_API_KEY` is missing or wrong. Re-check the backend environment tab.

### "Vectorstore empty" / long first-response time
- This is normal on free tier. The vector store auto-bootstraps on first
  request. Wait ~3 minutes and retry.

### Build fails: `ModuleNotFoundError`
- Run `pip install -r requirements.txt` locally and confirm all imports work.
- Check that `requirements.txt` is committed and up to date.

---

## Cost Summary (Render Free Tier)

| Service | Plan | Cost | Limitation |
|---|---|---|---|
| Backend (FastAPI) | Free | $0/mo | Spins down after 15 min idle; ephemeral disk |
| Frontend (Streamlit) | Free | $0/mo | Spins down after 15 min idle |
| Backend (FastAPI) | Starter | $7/mo | Always-on + 1 GB persistent disk for ChromaDB |
