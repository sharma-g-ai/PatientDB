from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import os
import shutil
from pathlib import Path

from app.models.patient import DocumentProcessingResult, PatientBase
from app.services.gemini_service import GeminiService
from app.models.patient import DocumentProcessingResultMulti

router = APIRouter()

# Dependency to get Gemini service
def get_gemini_service() -> GeminiService:
    return GeminiService()

@router.post("/upload", response_model=DocumentProcessingResult)
async def upload_document(
    file: UploadFile = File(...),
    gemini_service: GeminiService = Depends(get_gemini_service)
):
    """Upload and process a patient document"""
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'text/plain', 'application/pdf']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not supported. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Validate file size (10MB max)
    max_size = int(os.getenv("MAX_FILE_SIZE", 10485760))
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size too large. Maximum size: {max_size} bytes"
        )
    
    try:
        # Save file temporarily
        upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
        upload_dir.mkdir(exist_ok=True)
        
        safe_filename = file.filename or "uploaded_file"
        file_path = upload_dir / safe_filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Process document with Gemini
        result = await gemini_service.extract_patient_data(file_content, file.content_type)
        
        # Clean up temporary file
        if file_path.exists():
            file_path.unlink()
        
        return DocumentProcessingResult(
            extracted_data=PatientBase(
                name=result.get("name") or "Unknown",
                date_of_birth=result.get("date_of_birth") or "1900-01-01",
                diagnosis=result.get("diagnosis"),
                prescription=result.get("prescription")
            ),
            confidence_score=result.get("confidence_score", 0.0),
            raw_text=result.get("raw_text", "")
        )
        
    except Exception as e:
        # Clean up temporary file in case of error
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/supported-types")
async def get_supported_file_types():
    """Get list of supported file types"""
    return {
        "supported_types": [
            "image/jpeg",
            "image/png", 
            "image/jpg",
            "text/plain",
            "application/pdf"
        ],
        "max_file_size_bytes": int(os.getenv("MAX_FILE_SIZE", 10485760))
    }

@router.post("/upload-multiple", response_model=DocumentProcessingResultMulti)
async def upload_multiple_documents(
    files: list[UploadFile] = File(...),
    gemini_service: GeminiService = Depends(get_gemini_service)
):
    """Upload and process multiple patient documents in a single LLM context."""
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")

    allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'text/plain', 'application/pdf']
    max_size = int(os.getenv("MAX_FILE_SIZE", 10485760))

    # Validate all files and prepare payloads
    files_data = []
    total_bytes = 0
    for f in files:
        if f.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {f.content_type} not supported. Allowed types: {', '.join(allowed_types)}"
            )
        content = await f.read()
        total_bytes += len(content)
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File {f.filename} exceeds maximum size of {max_size} bytes"
            )
        files_data.append({
            "content": content,
            "name": f.filename or "uploaded_file",
            "type": f.content_type
        })

    try:
        # Single LLM call with all files via Gemini file upload API
        result = await gemini_service.extract_patient_data_from_multiple_files(files_data)

        # Map to a response shape similar to single-file result plus metadata
        return {
            "extracted_data": {
                "name": result.get("name") or "Unknown",
                "date_of_birth": result.get("date_of_birth") or "1900-01-01",
                "diagnosis": result.get("diagnosis"),
                "prescription": result.get("prescription")
            },
            "confidence_score": result.get("confidence_score", 0.0),
            "raw_text": result.get("raw_text", ""),
            "documents_processed": result.get("documents_processed", len(files)),
            "processing_method": result.get("processing_method"),
            "document_types": result.get("document_types"),
            "medical_history": result.get("medical_history"),
            "doctor_name": result.get("doctor_name"),
            "hospital_clinic": result.get("hospital_clinic")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")
