import os
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from .env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

# Config variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

# Resolve Chroma path relative to root if it is relative
chroma_path_raw = os.getenv("CHROMA_DB_PATH", "./data/chromadb")
if chroma_path_raw.startswith("./") or not os.path.isabs(chroma_path_raw):
    CHROMA_DB_PATH = str((ROOT_DIR / chroma_path_raw).resolve())
else:
    CHROMA_DB_PATH = chroma_path_raw

# Create directories
os.makedirs(ROOT_DIR / "data", exist_ok=True)
os.makedirs(os.path.dirname(CHROMA_DB_PATH), exist_ok=True)

def is_api_key_configured() -> bool:
    return bool(GEMINI_API_KEY)
