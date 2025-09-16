# backend/app/services/document_processor.py
import os
import uuid
import time
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
            
            # Check file size to log processing expectations
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            logger.info(f"Starting to process PDF of size {file_size_mb:.2f} MB: {filename}")
            
            # Load PDF with better error handling
            logger.info(f"Loading PDF: {file_path}")
            try:
                loader = PyPDFLoader(file_path)
                pages = loader.load()
                
                if not pages:
                    logger.warning(f"No pages found in {file_path}")
                    return {"success": False, "error": "No text content found in the PDF"}
                
                logger.info(f"Successfully loaded {len(pages)} pages from PDF")
            except Exception as e:
                logger.error(f"Error loading PDF: {str(e)}", exc_info=True)
                return {"success": False, "error": f"Failed to load PDF: {str(e)}"}
            
            # Split into chunks with better logging and handling for large files
            logger.info(f"Splitting {len(pages)} pages into chunks")
            
            # Process in batches for very large documents to avoid memory issues
            all_chunks = []
            batch_size = 10  # Process 10 pages at a time for very large docs
            
            if len(pages) > 50:  # For large documents
                logger.info(f"Large document detected ({len(pages)} pages). Processing in batches of {batch_size}.")
                
                for i in range(0, len(pages), batch_size):
                    batch_end = min(i + batch_size, len(pages))
                    logger.info(f"Processing batch of pages {i+1} to {batch_end} of {len(pages)}")
                    
                    batch_pages = pages[i:batch_end]
                    batch_chunks = self.text_splitter.split_documents(batch_pages)
                    
                    logger.info(f"Created {len(batch_chunks)} chunks from pages {i+1}-{batch_end}")
                    all_chunks.extend(batch_chunks)
                    
                    # Add a small delay to prevent potential memory issues
                    if len(pages) > 100:
                        time.sleep(0.1)
            else:
                # For smaller documents, process all at once
                all_chunks = self.text_splitter.split_documents(pages)
                logger.info(f"Created {len(all_chunks)} chunks")
            
            # Check if we have any chunks
            if not all_chunks:
                # Try a fallback method - extract text directly
                logger.warning(f"No chunks created from {file_path}. Attempting fallback text extraction.")
                
                fallback_chunks = []
                for i, page in enumerate(pages):
                    if page.page_content and len(page.page_content.strip()) > 0:
                        fallback_chunks.append(page)
                        logger.info(f"Extracted text directly from page {i+1}")
                
                if fallback_chunks:
                    logger.info(f"Fallback extraction successful. Got {len(fallback_chunks)} text chunks.")
                    all_chunks = fallback_chunks
                else:
                    logger.warning(f"Fallback extraction failed. No text content found in {file_path}")
                    return {"success": False, "error": "Failed to extract text from PDF. The file may be scanned or contain only images."}
            
            # Initialize vector store if needed
            if self.vector_store is None:
                logger.info("Initializing vector store")
                self.vector_store = FAISS.from_documents(all_chunks, self.embeddings)
            else:
                logger.info("Adding to existing vector store")
                self.vector_store.add_documents(all_chunks)
            
            # Store document metadata
            self.documents[doc_id] = {
                "filename": filename,
                "path": file_path,
                "num_pages": len(pages),
                "num_chunks": len(all_chunks),
                "file_size_mb": file_size_mb
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
                "num_chunks": len(all_chunks)
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