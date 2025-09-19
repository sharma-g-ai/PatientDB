# QUICK FIX for File Upload 422 Error
# This addresses the 422 Unprocessable Entity error when uploading files

# The issue is likely in the chat.py upload endpoint
# Add this import to the top of chat.py if it's missing:

import logging
logger = logging.getLogger(__name__)

# And make sure the upload endpoint has proper error handling:

@router.post("/upload-file")
async def upload_file_to_chat(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload a file to chat context - FIXED VERSION"""
    try:
        # Validate inputs
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        print(f"📁 Uploading file: {file.filename} to session: {session_id}")
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Add file to chat context
        file_data = {
            'name': file.filename,
            'type': file.content_type or 'application/octet-stream',
            'content': file_content
        }
        
        success = chat_context_service.add_attached_file(session_id, file_data)
        if not success:
            # Try to create session if it doesn't exist
            chat_context_service.create_session()  # This will return a new session_id
            success = chat_context_service.add_attached_file(session_id, file_data)
            
            if not success:
                raise HTTPException(status_code=404, detail="Could not attach file to session")
        
        print(f"✅ File uploaded successfully: {file.filename}")
        
        return {
            "success": True,
            "message": f"File '{file.filename}' uploaded successfully",
            "file_info": {
                "name": file.filename,
                "type": file.content_type or 'application/octet-stream',
                "size": len(file_content)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

# Apply this fix to your chat.py file