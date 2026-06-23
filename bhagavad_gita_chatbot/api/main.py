import os
import uuid
import datetime
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import shutil
from pathlib import Path

from utils.config import HOST, PORT, GEMINI_API_KEY, DATA_DIR
from utils.logger import logger
from vectorstore.database import gita_db
from services.upload_service import upload_service
from chains.rag_chain import GitaRAGChain

app = FastAPI(
    title="Bhagavad Gita AI Chatbot API",
    description="FastAPI Backend for Bhagavad Gita RAG-based AI Counseling Chatbot",
    version="1.0.0"
)

# Enable CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to store RAG chain and session memory
rag_chain: Optional[GitaRAGChain] = None
session_histories: Dict[str, List[Dict[str, str]]] = {}

# Uploads directory
UPLOAD_DIR = DATA_DIR / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Curated list of popular inspiring verses for "Verse of the Day"
POPULAR_VERSES = [
    {"chapter": 2, "verse": 20, "theme": "Immortality of the Soul"},
    {"chapter": 2, "verse": 47, "theme": "Karma Yoga - Performing duty without attachment to results"},
    {"chapter": 2, "verse": 50, "theme": "Equanimity in actions"},
    {"chapter": 3, "verse": 19, "theme": "Detached action leads to the supreme goal"},
    {"chapter": 3, "verse": 30, "theme": "Surrendering actions to the Divine"},
    {"chapter": 4, "verse": 7, "theme": "Descent of God to re-establish Dharma"},
    {"chapter": 4, "verse": 8, "theme": "Protection of the righteous and destruction of evil"},
    {"chapter": 6, "verse": 5, "theme": "Mind as one's friend or enemy"},
    {"chapter": 6, "verse": 6, "theme": "Conquering the mind"},
    {"chapter": 9, "verse": 22, "theme": "Divine protection and provision for true devotees"},
    {"chapter": 9, "verse": 26, "theme": "Offering with love and devotion"},
    {"chapter": 9, "verse": 27, "theme": "Dedication of all actions to God"},
    {"chapter": 12, "verse": 13, "theme": "Qualities of a true devotee - Friendship and Compassion"},
    {"chapter": 12, "verse": 14, "theme": "Equanimity and devotion"},
    {"chapter": 18, "verse": 54, "theme": "Attaining the state of supreme devotion"},
    {"chapter": 18, "verse": 61, "theme": "God residing in the hearts of all beings"},
    {"chapter": 18, "verse": 65, "theme": "Absorption in Divine thoughts"},
    {"chapter": 18, "verse": 66, "theme": "Surrender to the Supreme Lord"}
]

# Models for Request/Response Schemas
class ConfigRequest(BaseModel):
    gemini_api_key: str = Field(..., description="The Gemini API key to configure the service")

class ChatRequest(BaseModel):
    question: str = Field(..., description="User's query")
    session_id: Optional[str] = Field(None, description="Optional unique session identifier")
    history: Optional[List[Dict[str, str]]] = Field(None, description="Client-side message history overrides server-side memory")

class Citation(BaseModel):
    chapter: Optional[int] = None
    verse: Optional[int] = None
    source: str
    sanskrit: Optional[str] = None
    transliteration: Optional[str] = None
    translation: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    session_id: str

@app.on_event("startup")
def startup_event():
    """Attempts to initialize RAG chain on startup if key is configured in environment."""
    global rag_chain
    if GEMINI_API_KEY:
        try:
            logger.info("Initializing RAG chain from environment API key on startup...")
            rag_chain = GitaRAGChain(api_key=GEMINI_API_KEY)
            logger.info("RAG chain successfully initialized on startup.")
        except Exception as e:
            logger.error(f"Failed to initialize RAG chain on startup: {e}")
    else:
        logger.warning("No GEMINI_API_KEY found on startup. API requires /config initialization.")

def get_active_chain() -> GitaRAGChain:
    """Helper to retrieve the initialized RAG chain, throwing 400 if unconfigured."""
    global rag_chain
    if rag_chain is None:
        raise HTTPException(
            status_code=400,
            detail="Gemini API Key is not configured. Please supply a key via the '/config' endpoint first."
        )
    return rag_chain

@app.get("/status", summary="Check backend configuration status")
def status_endpoint():
    """Returns whether the backend is fully initialized with an API key and RAG chain."""
    global rag_chain
    return {"configured": rag_chain is not None}

@app.post("/config", summary="Configure Gemini API Key")
def configure_api_key(config: ConfigRequest):
    """Sets the API key at runtime and bootstraps the vector store."""
    global rag_chain
    try:
        logger.info("Configuring Gemini API key at runtime...")
        rag_chain = GitaRAGChain(api_key=config.gemini_api_key)
        # Update system-wide configuration values
        gita_db.init_db(config.gemini_api_key)
        logger.info("Successfully configured API key and initialized services.")
        return {"status": "success", "message": "Gemini API key configured and database initialized successfully."}
    except Exception as e:
        logger.error(f"Error configuring API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure API key: {str(e)}")

@app.post("/chat", response_model=ChatResponse, summary="Send message to RAG Chatbot")
def chat_endpoint(request: ChatRequest):
    """Answers query using RAG, managing session-based conversation history."""
    chain = get_active_chain()
    
    # Resolve or create session ID
    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        
    # Get conversation history
    if request.history is not None:
        history = request.history
    else:
        history = session_histories.get(session_id, [])
        
    try:
        # Generate RAG response
        answer, context_docs = chain.get_response(request.question, history)
        
        # Build Citations
        citations = []
        for doc in context_docs:
            meta = doc.metadata
            citations.append(Citation(
                chapter=meta.get("chapter"),
                verse=meta.get("verse"),
                source=meta.get("source", "Bhagavad Gita"),
                sanskrit=meta.get("sanskrit"),
                transliteration=meta.get("transliteration"),
                translation=meta.get("sivananda") or meta.get("adidevananda") or meta.get("gambirananda") or doc.page_content
            ))
            
        # Update server session history if not using custom client-side override
        if request.history is None:
            history.append({"role": "user", "content": request.question})
            history.append({"role": "assistant", "content": answer})
            session_histories[session_id] = history
            
        return ChatResponse(
            answer=answer,
            citations=citations,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"RAG Chain generation failed: {str(e)}")

@app.post("/clear_chat", summary="Clear session chat history")
def clear_chat_endpoint(session_id: str = Query(..., description="Session ID to clear")):
    """Clears history for the specified session ID."""
    if session_id in session_histories:
        session_histories[session_id] = []
        logger.info(f"Cleared chat history for session: {session_id}")
    return {"status": "success", "message": f"Chat history for session {session_id} has been cleared."}

@app.get("/search_verse", summary="Search for verses in Bhagavad Gita")
def search_verse_endpoint(
    query: str = Query(..., description="Search keyword or term"),
    chapter: Optional[int] = Query(None, description="Optional chapter filter (1-18)")
):
    """Searches local cached verses for query terms."""
    try:
        results = gita_db.search_local_verses(query, chapter)
        
        # Format response
        formatted_results = []
        for v in results:
            formatted_results.append({
                "chapter": v.get("chapter_number"),
                "verse": v.get("verse_number"),
                "title": v.get("title"),
                "sanskrit": v.get("text"),
                "transliteration": v.get("transliteration"),
                "word_meanings": v.get("word_meanings")
            })
        return {"count": len(formatted_results), "results": formatted_results}
    except Exception as e:
        logger.error(f"Error in search verse endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chapter_summary", summary="Get summary of a Bhagavad Gita Chapter")
def chapter_summary_endpoint(chapter: int = Query(..., description="Chapter number (1-18)")):
    """Returns details and summary of the specified chapter."""
    if not (1 <= chapter <= 18):
        raise HTTPException(status_code=400, detail="Chapter number must be between 1 and 18.")
        
    try:
        summary_info = gita_db.get_chapter_summary(chapter)
        if not summary_info:
            raise HTTPException(status_code=404, detail=f"Chapter {chapter} summary not found.")
            
        return {
            "chapter_number": summary_info.get("chapter_number"),
            "name": summary_info.get("name"),
            "name_meaning": summary_info.get("name_meaning"),
            "name_translation": summary_info.get("name_translation"),
            "verses_count": summary_info.get("verses_count"),
            "summary": summary_info.get("chapter_summary"),
            "summary_hindi": summary_info.get("chapter_summary_hindi")
        }
    except Exception as e:
        logger.error(f"Error in chapter summary endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/verse_of_the_day", summary="Get the curated Verse of the Day")
def verse_of_the_day_endpoint():
    """
    Returns the Verse of the Day based on calendar date.

    ROOT CAUSE FIX: The original implementation used search_local_verses() which
    searched for the string "Verse N" inside transliteration/title/text fields. When
    no verse contained that literal substring, verse_details fell back to None and a
    hardcoded Ch4V7 text was returned — while the chapter/verse numbers still reflected
    the selected POPULAR_VERSES entry (e.g. Ch12V13). This caused cross-verse mixing.

    FIX: Use get_full_verse_with_translations() which performs a direct exact match on
    (chapter_number, verse_number) and returns all fields atomically from one record.
    """
    try:
        # Determine verse index based on day of year
        day_of_year = datetime.date.today().timetuple().tm_yday
        selected = POPULAR_VERSES[day_of_year % len(POPULAR_VERSES)]

        ch_num = selected["chapter"]
        v_num  = selected["verse"]

        logger.info(f"Verse of the Day: Fetching Ch {ch_num}, V {v_num} — {selected['theme']}")

        # ATOMIC FETCH — all fields from the same verse record, zero mixing possible
        verse_data = gita_db.get_full_verse_with_translations(ch_num, v_num)

        if not verse_data:
            # Graceful fallback: try Ch2V47 (the most universally known verse)
            logger.warning(f"Ch {ch_num} V {v_num} not found — falling back to Ch2V47")
            ch_num, v_num = 2, 47
            selected = {"chapter": 2, "verse": 47, "theme": "Karma Yoga — Performing duty without attachment to results"}
            verse_data = gita_db.get_full_verse_with_translations(ch_num, v_num)

        if not verse_data:
            raise HTTPException(status_code=503, detail="Verse data unavailable. Dataset may still be downloading.")

        # ── Validation: confirm all fields belong to the same verse ──────────
        stored_ch = verse_data.get("chapter_number")
        stored_v  = verse_data.get("verse_number")
        if stored_ch != ch_num or stored_v != v_num:
            logger.error(
                f"VERSE MISMATCH DETECTED: requested Ch{ch_num}V{v_num} "
                f"but got Ch{stored_ch}V{stored_v} — aborting render"
            )
            raise HTTPException(status_code=500, detail="Verse data integrity check failed.")

        # Pick the best available translation (priority: Sivananda > Gambirananda > Purohit > Adidevananda)
        translation = (
            verse_data.get("sivananda")
            or verse_data.get("gambirananda")
            or verse_data.get("purohit")
            or verse_data.get("adidevananda")
            or verse_data.get("sankaranarayan")
            or "Translation not available."
        )

        return {
            "id":              verse_data.get("id"),
            "chapterNumber":   ch_num,
            "verseNumber":     v_num,
            "theme":           selected["theme"],
            "sanskrit":        verse_data.get("text", ""),
            "transliteration": verse_data.get("transliteration", ""),
            "wordMeanings":    verse_data.get("word_meanings", ""),
            "translation":     translation,
            # Legacy keys kept for backward compatibility with existing clients
            "chapter":         ch_num,
            "verse":           v_num,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in verse of the day: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/upload", summary="Upload a custom PDF or text file for indexing")
async def upload_file_endpoint(file: UploadFile = File(...)):
    """Uploads a PDF or text file, index it into ChromaDB, and clears file cache."""
    chain = get_active_chain()
    
    # Save the file temporarily
    temp_path = UPLOAD_DIR / file.filename
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process and index file in vectorstore
        chunks_count = upload_service.process_file(str(temp_path), chain.db)
        
        return {
            "status": "success",
            "message": f"Successfully loaded and split '{file.filename}' into {chunks_count} chunks, which are indexed into the database.",
            "file_name": file.filename,
            "chunks_count": chunks_count
        }
    except Exception as e:
        logger.error(f"Error processing file upload '{file.filename}': {e}")
        raise HTTPException(status_code=500, detail=f"File parsing/indexing failed: {str(e)}")
    finally:
        # Cleanup uploaded temp file
        if temp_path.exists():
            os.remove(temp_path)
            logger.info(f"Cleaned up temporary upload file path: {temp_path}")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting FastAPI backend server on {HOST}:{PORT}")
    uvicorn.run("api.main:app", host=HOST, port=PORT, reload=True)
