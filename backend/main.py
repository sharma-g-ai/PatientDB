from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from app.api import documents, patients, chat
from app.database import create_tables
from app.services.gemini_service import GeminiService
from app.services.rag_service import RAGService

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Patient Document Management API",
    description="API for managing patient documents with AI transcription and RAG chat",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables on startup
@app.on_event("startup")
def startup():
    create_tables()
    print("✅ Database tables created successfully!")

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Patient Document Management API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
