# backend/app/routers/documents.py
import os
import shutil
import logging
import traceback
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.document_processor import document_processor
from app.services.rag_service import rag_service  # Add this import


router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document (PDF) for processing"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save the file temporarily
    file_path = f"uploads/{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved to {file_path}")
        
        # Check file size
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size / (1024*1024):.2f} MB")
        
        # Process the document
        result = document_processor.process_pdf(file_path, file.filename)
        
        if not result.get("success", False):
            logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        logger.info(f"Document processed successfully: {result}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in upload_document: {str(e)}")
        logger.error(traceback.format_exc())
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/")
async def get_all_documents():
    """Get all processed documents"""
    return document_processor.get_all_documents()


@router.post("/{doc_id}/summarize")
async def summarize_document(doc_id: str):
    """Generate a summary of a document"""
    # Check if document exists
    documents = document_processor.get_all_documents()
    if doc_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Get document info
        doc_info = documents[doc_id]
        
        # Create a prompt for summarization
        prompt = f"""
        Please provide a concise summary of the document titled '{doc_info['filename']}'. 
        Focus on the main points, key findings, and important conclusions. 
        Structure the summary with bullet points for clarity.
        """
        
        # Use the RAG service to generate a summary
        logger.info(f"Generating summary for document: {doc_info['filename']}")
        result = rag_service.get_answer(prompt, include_sources=False)
        
        return {
            "doc_id": doc_id,
            "filename": doc_info['filename'],
            "summary": result["answer"]
        }
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}", exc_info=True)
        # Provide a fallback summary
        return {
            "doc_id": doc_id,
            "filename": documents[doc_id]['filename'],
            "summary": "This is a placeholder summary. The document contains information that would normally be summarized by the AI. Due to technical limitations with the current model configuration, a detailed summary could not be generated automatically."
        }