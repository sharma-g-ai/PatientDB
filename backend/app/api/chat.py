from fastapi import APIRouter, HTTPException, Depends
from app.models.patient import ChatMessage, ChatResponse
from app.services.direct_chat_service import DirectChatService

router = APIRouter()

# Dependency to get Direct Chat service
def get_chat_service() -> DirectChatService:
    return DirectChatService()

@router.post("/", response_model=ChatResponse)
async def chat_with_patients(
    message: ChatMessage,
    chat_service: DirectChatService = Depends(get_chat_service)
):
    """Chat with patient data using direct Gemini context"""
    try:
        # Generate response using direct approach
        result = await chat_service.generate_response(message.message)
        
        # Extract patient names from mentioned patients for sources
        sources = [patient["name"] for patient in result["mentioned_patients"]]
        patient_ids = [patient["id"] for patient in result["mentioned_patients"]]
        
        return ChatResponse(
            response=result["response"],
            sources=sources,
            patient_ids=patient_ids
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )

@router.get("/health")
async def chat_health_check(chat_service: DirectChatService = Depends(get_chat_service)):
    """Health check for chat service"""
    try:
        status = await chat_service.get_health_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat service health check failed: {str(e)}"
        )
