import os
import time
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.embeddings import Embeddings
import google.generativeai as genai

from utils.config import GEMINI_API_KEY
from utils.logger import logger

class RawGoogleGenAIEmbeddings(Embeddings):
    def __init__(self, model: str = "models/gemini-embedding-2", google_api_key: str = None):
        self.model = model
        self.google_api_key = google_api_key
        if google_api_key:
            genai.configure(api_key=google_api_key)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.google_api_key:
            raise ValueError("API Key is required to embed documents.")
        batch_size = 12
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = genai.embed_content(
                model=self.model,
                content=batch,
                task_type="retrieval_document"
            )
            results.extend(response['embedding'])
            if i + batch_size < len(texts):
                time.sleep(8.5) # Small delay between batches to respect rate limits
        return results

    def embed_query(self, text: str) -> List[float]:
        if not self.google_api_key:
            raise ValueError("API Key is required to embed queries.")
        response = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_query"
        )
        return response['embedding']

class GeminiService:
    def __init__(self):
        self._api_key = GEMINI_API_KEY
        if not self._api_key:
            logger.warning(
                "GEMINI_API_KEY or GOOGLE_API_KEY not found in environment. "
                "The services will fail to initialize unless keys are set globally."
            )
            
    def get_embeddings(self) -> RawGoogleGenAIEmbeddings:
        """Returns the custom Gemini embeddings generator."""
        logger.info("Initializing custom Gemini Embeddings (model: models/gemini-embedding-2)")
        try:
            return RawGoogleGenAIEmbeddings(
                model="models/gemini-embedding-2",
                google_api_key=self._api_key
            )
        except Exception as e:
            logger.error(f"Failed to initialize RawGoogleGenAIEmbeddings: {e}")
            raise e

    def get_llm(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.2) -> ChatGoogleGenerativeAI:
        """Returns the Gemini Chat model."""
        logger.info(f"Initializing Gemini LLM (model: {model_name}, temperature: {temperature})")
        try:
            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                google_api_key=self._api_key
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatGoogleGenerativeAI: {e}")
            raise e

# Singleton instance
gemini_service = GeminiService()
