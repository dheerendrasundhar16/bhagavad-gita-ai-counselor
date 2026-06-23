import os
import json
import time
import urllib.request
from typing import List, Dict, Optional
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document
from services.gemini_service import RawGoogleGenAIEmbeddings

from utils.config import CHROMA_DB_PATH, GEMINI_API_KEY, ROOT_DIR, DATA_DIR
from utils.logger import logger

os.makedirs(DATA_DIR, exist_ok=True)

# URL references for bootstrapping
URLS = {
    "chapters": "https://raw.githubusercontent.com/praneshp1org/Bhagavad-Gita-JSON-data/main/chapters.json",
    "verse": "https://raw.githubusercontent.com/praneshp1org/Bhagavad-Gita-JSON-data/main/verse.json",
    "translation": "https://raw.githubusercontent.com/praneshp1org/Bhagavad-Gita-JSON-data/main/translation.json"
}

class GitaDatabase:
    def __init__(self):
        self._db: Optional[Chroma] = None
        self._chapters_cache: Optional[List[Dict]] = None
        self._verses_cache: Optional[List[Dict]] = None
        
    def _download_file(self, name: str, url: str) -> Path:
        """Downloads a dataset file from GitHub if not already cached."""
        dest_path = DATA_DIR / f"{name}.json"
        if dest_path.exists():
            logger.info(f"Using cached file for {name} at {dest_path}")
            return dest_path
            
        logger.info(f"Downloading {name} dataset from {url}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8-sig')
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            logger.info(f"Successfully downloaded and cached {name} to {dest_path}")
            return dest_path
        except Exception as e:
            logger.error(f"Failed to download {name} dataset: {e}")
            raise e

    def load_cached_data(self) -> tuple[List[Dict], List[Dict], List[Dict]]:
        """Downloads (if needed) and parses all three JSON dataset files."""
        chapters_path = self._download_file("chapters", URLS["chapters"])
        verse_path = self._download_file("verse", URLS["verse"])
        translation_path = self._download_file("translation", URLS["translation"])
        
        with open(chapters_path, 'r', encoding='utf-8') as f:
            chapters = json.load(f)
        with open(verse_path, 'r', encoding='utf-8') as f:
            verses = json.load(f)
        with open(translation_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            
        return chapters, verses, translations

    def get_chapters(self) -> List[Dict]:
        """Returns the list of all chapters with metadata and summaries."""
        if self._chapters_cache is None:
            try:
                self._download_file("chapters", URLS["chapters"])
                chapters_path = DATA_DIR / "chapters.json"
                with open(chapters_path, 'r', encoding='utf-8') as f:
                    self._chapters_cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading chapters cache: {e}")
                return []
        return self._chapters_cache

    def get_chapter_summary(self, chapter_number: int) -> Optional[Dict]:
        """Fetches the summary and metadata for a specific chapter."""
        chapters = self.get_chapters()
        for ch in chapters:
            if ch.get("chapter_number") == chapter_number:
                return ch
        return None

    def get_verse_by_reference(self, chapter: int, verse: int) -> Optional[Dict]:
        """Fetches a specific verse by exact chapter and verse number from the local cache."""
        if self._verses_cache is None:
            try:
                self._download_file("verse", URLS["verse"])
                verse_path = DATA_DIR / "verse.json"
                with open(verse_path, 'r', encoding='utf-8') as f:
                    self._verses_cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading verses cache: {e}")
                return None

        for v in self._verses_cache:
            if v.get("chapter_number") == chapter and v.get("verse_number") == verse:
                return v
        return None

    def get_full_verse_with_translations(self, chapter: int, verse: int) -> Optional[Dict]:
        """Returns a verse dict merged with all its translations."""
        verse_data = self.get_verse_by_reference(chapter, verse)
        if not verse_data:
            return None

        _, _, translations = self.load_cached_data()
        v_id = verse_data.get("id")
        verse_translations: Dict[str, str] = {}
        for t in translations:
            if t.get("verse_id") == v_id:
                author = t.get("authorName", "")
                desc = t.get("description", "")
                if "Sivananda" in author:
                    verse_translations["sivananda"] = desc
                elif "Adidevananda" in author:
                    verse_translations["adidevananda"] = desc
                elif "Gambirananda" in author:
                    verse_translations["gambirananda"] = desc
                elif "Purohit" in author:
                    verse_translations["purohit"] = desc
                elif "Sankaranarayan" in author:
                    verse_translations["sankaranarayan"] = desc

        return {**verse_data, **verse_translations}

    def search_local_verses(self, query: str, chapter: Optional[int] = None) -> List[Dict]:
        """Searches local cached verses for simple metadata querying."""
        # Ensure verses cache is loaded
        if self._verses_cache is None:
            try:
                self._download_file("verse", URLS["verse"])
                verse_path = DATA_DIR / "verse.json"
                with open(verse_path, 'r', encoding='utf-8') as f:
                    self._verses_cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading verses cache: {e}")
                return []
                
        results = []
        query_lower = query.lower()
        for v in self._verses_cache:
            if chapter is not None and v.get("chapter_number") != chapter:
                continue
            
            # Check matches in transliteration or title
            translit = v.get("transliteration", "").lower()
            title = v.get("title", "").lower()
            text = v.get("text", "").lower()
            
            if query_lower in translit or query_lower in title or query_lower in text:
                results.append(v)
        return results

    def init_db(self, api_key: Optional[str] = None) -> Chroma:
        """Initializes the Chroma DB, boots it up, and populates it if empty."""
        if self._db is not None:
            return self._db

        active_key = api_key or GEMINI_API_KEY
        if not active_key:
            logger.error("Database initialization failed: No API Key provided.")
            raise ValueError("Google Gemini API Key is required to initialize the database.")

        logger.info(f"Initializing Chroma DB at: {CHROMA_DB_PATH}")
        embeddings = RawGoogleGenAIEmbeddings(
            model="models/gemini-embedding-2",
            google_api_key=active_key
        )

        self._db = Chroma(
            collection_name="bhagavad_gita",
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_PATH
        )

        # Check if database is empty by counting collection documents
        try:
            coll_cnt = len(self._db.get()["ids"])
            logger.info(f"Found {coll_cnt} documents in existing collection.")
            if coll_cnt == 0:
                logger.info("Chroma DB collection is empty. Bootstrapping Gita dataset...")
                self._bootstrap_database(active_key)
        except Exception as e:
            logger.info(f"Chroma collection check or bootstrapping failed: {e}. Attempting full bootstrap...")
            self._bootstrap_database(active_key)

        return self._db

    def _bootstrap_database(self, api_key: str):
        """Processes the JSON files and loads them into Chroma."""
        logger.info("Loading dataset files...")
        chapters, verses, translations = self.load_cached_data()
        
        # Group translations by (verse_number, chapter_id or similar relation)
        # Looking at translation data: it has verse_id and verse_number.
        # Let's map translations by verse_id, which matches the verse's id in verse.json.
        translations_by_verse_id = {}
        for trans in translations:
            v_id = trans.get("verse_id")
            if v_id not in translations_by_verse_id:
                translations_by_verse_id[v_id] = []
            translations_by_verse_id[v_id].append(trans)
            
        documents = []
        logger.info("Parsing verses and compiling search documents...")
        
        for verse in verses:
            v_id = verse.get("id")
            v_num = verse.get("verse_number")
            ch_num = verse.get("chapter_number")
            sanskrit = verse.get("text", "")
            translit = verse.get("transliteration", "")
            
            # Find translations for this verse
            verse_trans = translations_by_verse_id.get(v_id, [])
            
            # We want translations by authors specifically:
            sivananda = ""
            adidevananda = ""
            gambirananda = ""
            purohit = ""
            sankaranarayan = ""
            
            for t in verse_trans:
                author = t.get("authorName")
                desc = t.get("description", "")
                if "Sivananda" in author:
                    sivananda = desc
                elif "Adidevananda" in author:
                    adidevananda = desc
                elif "Gambirananda" in author:
                    gambirananda = desc
                elif "Purohit" in author:
                    purohit = desc
                elif "Sankaranarayan" in author:
                    sankaranarayan = desc

            # Combine page content to optimize search retrieval
            page_content = (
                f"Chapter {ch_num}, Verse {v_num}\n"
                f"Sanskrit: {sanskrit}\n"
                f"Transliteration: {translit}\n"
                f"Swami Sivananda Translation: {sivananda}\n"
                f"Swami Adidevananda Translation: {adidevananda}\n"
                f"Swami Gambirananda Translation: {gambirananda}\n"
                f"Shri Purohit Swami Translation: {purohit}\n"
                f"Dr. S. Sankaranarayan Translation: {sankaranarayan}"
            )
            
            metadata = {
                "chapter": ch_num,
                "verse": v_num,
                "verse_id": v_id,
                "source": f"Gita {ch_num}.{v_num}",
                "sanskrit": sanskrit,
                "transliteration": translit,
                "sivananda": sivananda,
                "adidevananda": adidevananda,
                "gambirananda": gambirananda,
                "purohit": purohit,
                "sankaranarayan": sankaranarayan
            }
            
            documents.append(Document(page_content=page_content, metadata=metadata))
            
        logger.info(f"Adding {len(documents)} Gita verses to vector store in chunks...")
        # Add to vector store in larger chunks now that we use the custom batched embeddings class
        chunk_size = 100
        for i in range(0, len(documents), chunk_size):
            chunk = documents[i:i + chunk_size]
            self._db.add_documents(chunk)
            logger.info(f"Indexed verses {i+1} to {min(i + chunk_size, len(documents))}")
            if i + chunk_size < len(documents):
                logger.info("Sleeping for 2 seconds to respect API rate limits...")
                time.sleep(2)
            
        logger.info("Bhagavad Gita database bootstrapping complete!")

# Singleton instance
gita_db = GitaDatabase()
