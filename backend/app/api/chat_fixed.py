from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import Optional, List
import json

from ..services.gemini_service import GeminiService
from ..services.chat_context_service import chat_context_service

router = APIRouter()

def get_gemini_service():
    return GeminiService()

@router.post("/start-session")
async def start_chat_session():
    """Start a new chat session"""
    session_id = chat_context_service.create_session()
    return {"session_id": session_id}

@router.post("/upload-file")
async def upload_file_to_chat(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload a file to chat context"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Add file to chat context
        file_data = {
            'name': file.filename,
            'type': file.content_type,
            'content': file_content
        }
        
        success = chat_context_service.add_attached_file(session_id, file_data)
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return {
            "success": True,
            "message": f"File '{file.filename}' uploaded successfully",
            "file_info": {
                "name": file.filename,
                "type": file.content_type,
                "size": len(file_content)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.post("/chat")
async def chat_with_context(
    session_id: str = Form(...),
    query: str = Form(...),
    patient_context: Optional[str] = Form(None),
    gemini_service: GeminiService = Depends(get_gemini_service)
):
    """Chat with file context support"""
    try:
        # Get chat context
        context = chat_context_service.get_context(session_id)
        if not context:
            # Create new session if not found
            session_id = chat_context_service.create_session()
            context = chat_context_service.get_context(session_id)
        
        # Add user message to context
        chat_context_service.add_message(session_id, query, 'user')
        
        # Get attached files
        attached_files = chat_context_service.get_attached_files(session_id)
        
        # Prepare context for LLM
        base_context = patient_context or "No patient data available."
        if context:
            previous_context = context.get('context_summary', '')
            full_context = f"{base_context}\n\nPrevious conversation context: {previous_context}"
        else:
            full_context = base_context
        
        # Generate response with file attachments
        if attached_files:
            response = await gemini_service.generate_chat_response_with_files(
                query=query,
                context=full_context,
                attached_files=attached_files
            )
        else:
            response = await gemini_service.generate_chat_response(
                query=query,
                context=full_context
            )
        
        # Add assistant response to context
        chat_context_service.add_message(session_id, response, 'assistant')
        
        # Update context summary (keep last 5 exchanges for context)
        if context:
            messages = context['messages'][-10:]  # Keep last 10 messages
            context_summary = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            chat_context_service.update_context_summary(session_id, context_summary)
        
        return {
            "response": response,
            "session_id": session_id,
            "attached_files_count": len(attached_files)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@router.get("/session/{session_id}/files")
async def get_session_files(session_id: str):
    """Get all files attached to a chat session"""
    try:
        attached_files = chat_context_service.get_attached_files(session_id)
        
        # Return file info without content
        file_list = []
        for file_data in attached_files:
            file_list.append({
                "file_id": file_data.get('file_id'),
                "name": file_data.get('name'),
                "type": file_data.get('type'),
                "uploaded_at": file_data.get('uploaded_at'),
                "size": len(file_data.get('content', b''))
            })
        
        return {"files": file_list}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session files: {str(e)}")

@router.delete("/session/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear a chat session"""
    success = chat_context_service.clear_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"success": True, "message": "Session cleared successfully"}

@router.get("/sessions")
async def get_chat_sessions():
    """Get list of all chat sessions"""
    sessions = chat_context_service.get_session_list()
    return {"sessions": sessions}

# Legacy endpoint for basic chat without files (for backward compatibility)
@router.post("/")
async def basic_chat(
    request: dict,
    gemini_service: GeminiService = Depends(get_gemini_service)
):
    """Basic chat endpoint for backward compatibility"""
    try:
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        response = await gemini_service.generate_chat_response(
            query=message,
            context="No specific patient context provided."
        )
        
        return {"response": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")