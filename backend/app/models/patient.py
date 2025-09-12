from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PatientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: str = Field(..., description="Date in YYYY-MM-DD format")
    diagnosis: Optional[str] = Field(None, max_length=500)
    prescription: Optional[str] = Field(None, max_length=1000)

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[str] = None
    diagnosis: Optional[str] = Field(None, max_length=500)
    prescription: Optional[str] = Field(None, max_length=1000)

class Patient(PatientBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DocumentProcessingResult(BaseModel):
    extracted_data: PatientBase
    confidence_score: float = Field(..., ge=0, le=1)
    raw_text: str

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    patient_ids: List[str] = []
