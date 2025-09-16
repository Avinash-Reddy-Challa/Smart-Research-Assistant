# backend/app/routers/chat.py
from fastapi import APIRouter, Body
from app.services.rag_service import rag_service
from pydantic import BaseModel

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

class QuestionRequest(BaseModel):
    question: str
    include_sources: bool = True

@router.post("/")
async def ask_question(request: QuestionRequest):
    """Ask a question to the RAG system"""
    result = rag_service.get_answer(request.question, request.include_sources)
    return result