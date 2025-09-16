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

    def process_pdf(self, file_path, filename):
        """Process a PDF document and store its chunks in the vector store"""
        try:
            doc_id = str(uuid.uuid4())
            
            # Load PDF
            logger.info(f"Loading PDF: {file_path}")
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            
            if not pages:
                logger.warning(f"No pages found in {file_path}")
                return {"success": False, "error": "No text content found in the PDF"}
            
            # Split into chunks
            logger.info(f"Splitting {len(pages)} pages into chunks")
            chunks = self.text_splitter.split_documents(pages)
            
            if not chunks:
                logger.warning(f"No chunks created from {file_path}")
                return {"success": False, "error": "Failed to extract text from PDF"}
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # Initialize vector store if needed
            if self.vector_store is None:
                logger.info("Initializing vector store")
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            else:
                logger.info("Adding to existing vector store")
                self.vector_store.add_documents(chunks)
            
            # Store document metadata
            self.documents[doc_id] = {
                "filename": filename,
                "path": file_path,
                "num_pages": len(pages),
                "num_chunks": len(chunks)
            }
            
            # Remove the temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Removed temporary file: {file_path}")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "filename": filename,
                "num_pages": len(pages),
                "num_chunks": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
            
            # Clean up
            if os.path.exists(file_path):
                os.remove(file_path)
                
            return {"success": False, "error": str(e)}
    
    def get_all_documents(self):
        """Get a list of all processed documents"""
        return self.documents
    
    def get_relevant_documents(self, query, k=4):
        """Get relevant document chunks for a query"""
        if self.vector_store is None:
            logger.warning("No documents in vector store")
            return []
            
        try:
            logger.info(f"Retrieving relevant documents for query: {query}")
            docs = self.vector_store.similarity_search(query, k=k)
            logger.info(f"Found {len(docs)} relevant documents")
            return docs
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}", exc_info=True)
            return []

# Create a singleton instance
document_processor = DocumentProcessor()