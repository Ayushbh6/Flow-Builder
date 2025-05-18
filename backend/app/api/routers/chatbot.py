from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
from json.decoder import JSONDecodeError

from app.db.session import get_db
from app.services.chatbot_service import ChatbotService
from app.core.config import settings

router = APIRouter()
chatbot_service = ChatbotService()

@router.post("/chat")
async def chat(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Process a chat message and return a response
    """
    # Check if API keys are set
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    if not settings.PINECONE_API_KEY:
        raise HTTPException(status_code=500, detail="Pinecone API key not configured")
    
    try:
        # Parse JSON request body
        data = await request.json()
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON request body")
        
    # Check if message exists
    message = data.get("message")
    history = data.get("history", [])
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        # Process chat message
        response = chatbot_service.chat(history, message)
        
        return {"response": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@router.post("/chat/stream")
async def chat_stream(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Process a chat message and stream the response
    """
    # Check if API keys are set
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    if not settings.PINECONE_API_KEY:
        raise HTTPException(status_code=500, detail="Pinecone API key not configured")
    
    try:
        # Parse JSON request body
        data = await request.json()
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON request body")
        
    # Check if message exists
    message = data.get("message")
    history = data.get("history", [])
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        # Define the streaming response function
        async def response_stream():
            async for chunk in chatbot_service.process_chat(history, message):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            response_stream(),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@router.get("/status")
async def check_status(db: Session = Depends(get_db)):
    """
    Check if the chatbot service is ready (API keys are configured)
    """
    status = {
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "pinecone_configured": bool(settings.PINECONE_API_KEY),
        "ready": bool(settings.OPENAI_API_KEY and settings.PINECONE_API_KEY)
    }
    
    return status 