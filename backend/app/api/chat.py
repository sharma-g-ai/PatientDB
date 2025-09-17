from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List
import json
import re
from app.models.patient import ChatMessage, ChatResponse
from app.services.rag_service import RAGService
from app.services.gemini_service import GeminiService
from app.services.database_service import DatabaseService
from app.database import SessionLocal

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

@router.post("/simple", response_model=ChatResponse)
async def simple_chat(
    message: str = Form(...),
    files: List[UploadFile] = File(default=[])
):
    """Simple chat: build context from all patients + uploaded files and ask LLM.
    No vector DB/RAG; just concatenates data into one prompt.
    """
    try:
        # 1) Gather all patients from DB
        db = SessionLocal()
        try:
            db_service = DatabaseService(db)
            patients = db_service.get_all_patients()
        finally:
            db.close()

        patients_context_parts: List[str] = []
        for i, p in enumerate(patients):
            patients_context_parts.append(
                f"Patient {i+1}: Name={p.name}; DOB={p.date_of_birth}; Diagnosis={p.diagnosis or ''}; Prescription={p.prescription or ''}"
            )
        patients_context = "\n".join(patients_context_parts) if patients_context_parts else "(No patients in database)"

        # Lightweight name detection from user message to prioritize relevant people
        mentioned_patients = []
        if patients:
            msg_lower = message.lower()
            # split into words and also try full-name containment
            for p in patients:
                name = (p.name or "").strip()
                if not name:
                    continue
                if name.lower() in msg_lower or any(token and token in name.lower() for token in re.findall(r"[a-zA-Z]+", msg_lower)):
                    mentioned_patients.append(p)
        # De-duplicate while preserving order
        seen_ids = set()
        mentioned_patients = [p for p in mentioned_patients if not (p.id in seen_ids or seen_ids.add(p.id))]

        # 2) Extract raw text from any uploaded files (best-effort)
        documents_text = ""
        if files:
            gemini = GeminiService()
            files_data = []
            for f in files:
                content = await f.read()
                files_data.append({
                    "content": content,
                    "name": f.filename,
                    "type": f.content_type or "application/octet-stream"
                })
            try:
                parsed = await gemini.extract_patient_data_from_multiple_files(files_data)
                documents_text = parsed.get("raw_text", "")
            except Exception:
                # Fallback: concatenate plain bytes decode
                texts: List[str] = []
                for fd in files_data:
                    try:
                        texts.append(fd["content"].decode("utf-8", errors="ignore"))
                    except Exception:
                        continue
                documents_text = "\n\n".join(texts)

        # 3) Build context
        context_sections = [
            "SYSTEM INSTRUCTIONS:\nYou are a medical assistant. Prefer database facts when answering questions about people. If the user asks about a patient by name, extract their details from the 'Focused Patients' or 'All Patients' sections below and answer precisely. If multiple patients match, present a concise list. If none match, say you don't have that person in the database.",
        ]
        if mentioned_patients:
            focused_parts: List[str] = []
            for p in mentioned_patients:
                focused_parts.append(
                    f"Name={p.name}; DOB={p.date_of_birth}; Diagnosis={p.diagnosis or ''}; Prescription={p.prescription or ''}; ID={p.id}"
                )
            context_sections.extend(["\nFocused Patients:", "\n".join(focused_parts)])
        # Always include a compact JSON for structured parsing if needed
        context_sections.extend([
            "\nAll Patients (compact list):",
            patients_context,
            "\nAll Patients (JSON):",
            json.dumps([
                {
                    "id": p.id,
                    "name": p.name,
                    "date_of_birth": p.date_of_birth,
                    "diagnosis": p.diagnosis,
                    "prescription": p.prescription,
                }
                for p in patients
            ][:100], ensure_ascii=False),  # cap to first 100 to keep prompt size reasonable
        ])
        if documents_text.strip():
            context_sections.extend(["\nUploaded Documents (raw text):", documents_text[:20000]])  # cap to 20k chars
        full_context = "\n".join(context_sections)

        # 4) Call LLM
        gemini = GeminiService()
        llm_response = await gemini.generate_chat_response(message, full_context)

        # Structured header for matched patients
        if mentioned_patients:
            header_lines = [
                "I found the following patients matching your query:",
                ""
            ]
            for idx, p in enumerate(mentioned_patients, start=1):
                header_lines.extend([
                    f"{idx}. Name: {p.name}",
                    f"   DOB: {p.date_of_birth}",
                    f"   Diagnosis: {p.diagnosis or '-'}",
                    f"   Prescription: {p.prescription or '-'}",
                    f"   ID: {p.id}",
                    ""
                ])
            header = "\n".join(header_lines)
        else:
            header = ""

        # Surface DB people back to client as sources when mentioned
        src_names = [p.name for p in mentioned_patients]
        src_ids = [p.id for p in mentioned_patients]

        # Build structured matched_patients payload
        matched_payload = [
            {
                "id": p.id,
                "name": p.name,
                "date_of_birth": p.date_of_birth,
                "diagnosis": p.diagnosis,
                "prescription": p.prescription,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            for p in mentioned_patients
        ]

        return ChatResponse(
            response=header + llm_response,
            sources=src_names,
            patient_ids=src_ids,
            matched_patients=matched_payload,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in simple chat: {str(e)}")

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
