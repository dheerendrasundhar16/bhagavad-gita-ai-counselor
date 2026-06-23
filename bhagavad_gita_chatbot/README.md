# 🕉️ Bhagavad Gita AI Counselor

> *"Whenever there is a decline in righteousness… I manifest Myself."* — Bhagavad Gita 4.7

A production-ready **Retrieval-Augmented Generation (RAG)** chatbot that provides spiritual guidance rooted exclusively in the authentic teachings of the Bhagavad Gita. Built with **FastAPI**, **Streamlit**, **LangChain**, and **Google Gemini**.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-0.2-purple)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-orange)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

| Feature | Details |
|---|---|
| 🤖 **AI Counselor** | Answers questions strictly from Bhagavad Gita teachings |
| 📜 **Verse of the Day** | Curated daily verse with Sanskrit, transliteration & translation |
| 📖 **Chapter Explorer** | Browse all 18 chapters with summaries |
| 🔍 **Verse Search** | Full-text keyword search across all 701 verses |
| 💬 **Session Memory** | Conversation history with context-aware follow-ups |
| 🌟 **Emotion Cards** | Quick starters for Anxiety, Fear, Confusion, Loneliness, and more |
| 📚 **Custom Upload** | Index your own PDF/TXT Gita commentaries |
| 🔄 **Auto-Bootstrap** | Vector store auto-builds on first run — no manual data setup |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Render (Production)                      │
│                                                              │
│  ┌───────────────────────┐   ┌───────────────────────────┐  │
│  │  Streamlit Frontend   │──▶│    FastAPI Backend         │  │
│  │  gita-counselor-      │   │  gita-counselor-backend    │  │
│  │  frontend             │   │  /chat  /search_verse      │  │
│  │  (port $PORT)         │   │  /verse_of_the_day         │  │
│  └───────────────────────┘   └───────────┬───────────────┘  │
│                                          │                   │
│                              ┌───────────▼───────────────┐  │
│                              │   LangChain RAG Chain      │  │
│                              │   ChromaDB  │  Gemini LLM  │  │
│                              └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Request flow:**
1. User sends a question in Streamlit
2. Streamlit POSTs to FastAPI `/chat`
3. FastAPI rephrases query → retrieves top-K verses from ChromaDB
4. Gemini LLM generates a structured, verse-grounded response
5. Streamlit renders the response as rich HTML cards

---

## 📂 Project Structure

```
bhagavad_gita_chatbot/
│
├── app.py                    # Streamlit frontend (UI, CSS, chat logic)
├── api/
│   └── main.py               # FastAPI server (routes, session memory)
├── chains/
│   ├── prompts.py            # System + history-aware RAG prompts
│   └── rag_chain.py          # Conversational RAG pipeline
├── vectorstore/
│   └── database.py           # ChromaDB connection + auto-bootstrap
├── services/
│   ├── gemini_service.py     # Gemini LLM + Embeddings wrapper
│   └── upload_service.py     # PDF/TXT chunker and indexer
├── utils/
│   ├── config.py             # Environment variable loader
│   └── logger.py             # Structured logger
├── data/                     # Auto-created: JSON cache + ChromaDB store
├── tests/                    # pytest test suite
│
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Project metadata + build config
├── render.yaml               # Render Blueprint (backend + frontend)
├── Dockerfile                # Backend container (FastAPI)
├── Dockerfile.streamlit      # Frontend container (Streamlit)
├── docker-compose.yml        # Local full-stack development
├── .env.example              # Template for environment variables
├── .streamlit/config.toml    # Streamlit theme + server settings
└── .github/workflows/ci.yml  # GitHub Actions CI (lint + test)
```

---

## 🚀 Quick Start — Local Development

### Prerequisites
- Python 3.10+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/bhagavad-gita-ai-counselor.git
cd bhagavad-gita-ai-counselor
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set your Gemini API key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
BACKEND_URL=http://127.0.0.1:8000
CHROMA_DB_PATH=./data/chromadb
```

### 5. Start the FastAPI backend

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

The API docs are available at → `http://127.0.0.1:8000/docs`

### 6. Start the Streamlit frontend (new terminal)

```bash
streamlit run app.py
```

Open your browser → `http://localhost:8501`

> **First run:** The vectorstore auto-downloads all 701 Bhagavad Gita verses from GitHub and indexes them. This takes ~2–3 minutes. Subsequent starts are instant.

---

## 🐳 Local Docker (Full Stack)

Run both services with a single command:

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Streamlit Frontend | http://localhost:8501 |
| FastAPI Backend | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## ☁️ Deployment on Render

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for the complete, step-by-step guide.

**Summary:**
- The `render.yaml` Blueprint deploys **both services** (backend + frontend) automatically from your GitHub repository.
- `GEMINI_API_KEY` and `BACKEND_URL` are set securely in the Render dashboard — never committed to the repo.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/status` | Health check — returns `{"configured": true}` |
| `POST` | `/chat` | Main RAG chat endpoint |
| `GET` | `/verse_of_the_day` | Today's curated Gita verse |
| `GET` | `/chapter_summary?chapter=N` | Summary for chapter 1–18 |
| `GET` | `/search_verse?query=karma` | Full-text verse search |
| `POST` | `/clear_chat?session_id=...` | Clear session history |
| `POST` | `/upload` | Upload PDF/TXT for indexing |

Full interactive docs: `http://127.0.0.1:8000/docs`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit 1.35+ |
| **Backend** | FastAPI 0.111+ + Uvicorn |
| **RAG Pipeline** | LangChain 0.2 |
| **Vector Database** | ChromaDB 0.5 |
| **LLM + Embeddings** | Google Gemini (`gemini-1.5-flash` + `models/embedding-001`) |
| **Document Parsing** | PyPDFLoader, TextLoader, RecursiveCharacterTextSplitter |
| **Deployment** | Render (Blueprint) |
| **CI** | GitHub Actions |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.
