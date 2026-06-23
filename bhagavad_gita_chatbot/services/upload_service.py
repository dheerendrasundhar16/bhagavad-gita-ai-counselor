import os
from pathlib import Path
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from utils.logger import logger

class UploadService:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True
        )

    def process_file(self, file_path: str, db: Chroma) -> int:
        """Loads, splits, and embeds an uploaded PDF or Text file.
        
        Args:
            file_path: Absolute path to the file.
            db: Target Chroma DB instance.
            
        Returns:
            int: Number of chunks added to the vector store.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found at: {file_path}")
            
        suffix = path.suffix.lower()
        logger.info(f"Processing uploaded file {path.name} (type: {suffix})")
        
        # Select appropriate document loader
        if suffix == ".pdf":
            loader = PyPDFLoader(str(path))
        elif suffix in [".txt", ".text"]:
            loader = TextLoader(str(path), encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file type '{suffix}'. Only PDF and TXT files are allowed.")
            
        try:
            # Load docs
            raw_docs = loader.load()
            logger.info(f"Loaded {len(raw_docs)} raw pages/documents from {path.name}")
            
            # Split docs
            split_docs = self.splitter.split_documents(raw_docs)
            logger.info(f"Split into {len(split_docs)} text chunks.")
            
            # Update metadata to ensure source is trackable
            for doc in split_docs:
                doc.metadata["source"] = f"Uploaded File: {path.name}"
                doc.metadata["is_uploaded"] = True
                
            # Add to DB in batches to prevent API rate limit issues
            batch_size = 100
            for i in range(0, len(split_docs), batch_size):
                batch = split_docs[i:i + batch_size]
                db.add_documents(batch)
                
            logger.info(f"Successfully indexed all chunks from {path.name} into ChromaDB.")
            return len(split_docs)
            
        except Exception as e:
            logger.error(f"Error indexing uploaded file {path.name}: {e}")
            raise e

# Singleton instance
upload_service = UploadService()
