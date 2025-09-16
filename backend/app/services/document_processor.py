# backend/app/services/document_processor.py
import os
import uuid
import logging
import numpy as np
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from app.utils.grok_integration import SimpleEmbeddings
from app.config import GROK_API_KEY  # Import from config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Use SimpleEmbeddings directly since Grok doesn't support the embedding model we need
        self.embeddings = SimpleEmbeddings()
        logger.info("DocumentProcessor initialized with SimpleEmbeddings")
            
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.vector_store = None
        self.documents = {}  # To track documents and their metadata

    # Rest of the class remains the same...