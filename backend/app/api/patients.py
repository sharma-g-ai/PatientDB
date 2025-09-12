from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.models.patient import Patient, PatientCreate, PatientUpdate
from app.services.database_service import DatabaseService, get_database_service
from app.services.rag_service import RAGService
from app.database import get_db

router = APIRouter()

# Dependency to get RAG service
def get_rag_service() -> RAGService:
    return RAGService()

@router.post("/", response_model=Patient, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Create a new patient record"""
    try:
        db_service = DatabaseService(db)
        
        # Create patient in database
        patient = db_service.create_patient(patient_data)
        
        # Add to vector store for RAG
        try:
            patient_dict = {
                "id": patient.id,
                "name": patient.name,
                "date_of_birth": patient.date_of_birth,
                "diagnosis": patient.diagnosis,
                "prescription": patient.prescription
            }
            await rag_service.add_patient_to_vector_store(patient_dict)
        except Exception as e:
            print(f"Warning: Failed to add patient to vector store: {e}")
        
        return patient
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating patient: {str(e)}"
        )

@router.get("/", response_model=List[Patient])
async def get_all_patients(db: Session = Depends(get_db)):
    """Get all patient records"""
    try:
        db_service = DatabaseService(db)
        return db_service.get_all_patients()
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching patients: {str(e)}"
        )

@router.get("/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get a specific patient by ID"""
    try:
        db_service = DatabaseService(db)
        patient = db_service.get_patient_by_id(patient_id)
        
        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient not found"
            )
        
        return patient
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching patient: {str(e)}"
        )

@router.put("/{patient_id}", response_model=Patient)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Update a patient record"""
    try:
        db_service = DatabaseService(db)
        
        # Update patient in database
        updated_patient = db_service.update_patient(patient_id, patient_update)
        
        if not updated_patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Update vector store
        try:
            patient_dict = {
                "id": updated_patient.id,
                "name": updated_patient.name,
                "date_of_birth": updated_patient.date_of_birth,
                "diagnosis": updated_patient.diagnosis,
                "prescription": updated_patient.prescription
            }
            await rag_service.add_patient_to_vector_store(patient_dict)
        except Exception as e:
            print(f"Warning: Failed to update patient in vector store: {e}")
        
        return updated_patient
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating patient: {str(e)}"
        )

@router.delete("/{patient_id}")
async def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    """Delete a patient record"""
    try:
        db_service = DatabaseService(db)
        
        # Delete from database
        success = db_service.delete_patient(patient_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {"message": "Patient deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting patient: {str(e)}"
        )
