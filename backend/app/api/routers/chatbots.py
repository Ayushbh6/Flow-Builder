from fastapi import APIRouter

# Import the router from chatbot.py
from app.api.routers.chatbot import router

# This is just a re-export to maintain compatibility with the api.py imports

@router.get("/")
def get_chatbots():
    """
    Get all chatbots
    """
    # To be implemented
    return {"message": "Get all chatbots - to be implemented"} 