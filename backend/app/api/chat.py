from fastapi import APIRouter, HTTPException, Depends
from app.models.patient import ChatMessage, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter()

# Dependency to get RAG service
def get_rag_service() -> RAGService:
    return RAGService()

@router.post("/", response_model=ChatResponse)
async def chat_with_patients(
    message: ChatMessage,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Chat with patient data using RAG"""
    try:
        # Generate response using RAG with optional upload_batch_id to include staging
        rag_result = await rag_service.generate_rag_response(message.message, upload_batch_id=message.upload_batch_id)
        
        return ChatResponse(
            response=rag_result["response"],
            sources=rag_result["sources"],
            patient_ids=rag_result["patient_ids"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )

@router.post("/refresh-knowledge-base")
async def refresh_knowledge_base(rag_service: RAGService = Depends(get_rag_service)):
    """Refresh the RAG knowledge base with all patient data"""
    try:
        await rag_service.refresh_vector_store()
        return {"message": "Knowledge base refreshed successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing knowledge base: {str(e)}"
        )

@router.get("/health")
async def chat_health_check():
    """Health check for chat service"""
    return {"status": "Chat service is healthy"}
