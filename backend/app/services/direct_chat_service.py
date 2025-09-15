from typing import Dict, Any, List
from app.services.database_service import DatabaseService
from app.services.gemini_service import GeminiService
from app.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class DirectChatService:
    """Simple, direct chat service using Gemini's large context window"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
    
    async def generate_response(self, query: str) -> Dict[str, Any]:
        """Generate chat response by passing all patient data directly to Gemini"""
        try:
            # Get all patients from database
            patients_data = self._get_all_patients()
            
            # Generate response using Gemini with full context
            result = await self.gemini_service.generate_chat_response(query, patients_data)
            
            return {
                "response": result["response"],
                "mentioned_patients": result["mentioned_patients"],
                "total_patients": result["total_patients_in_context"],
                "context_method": "direct_gemini"
            }
            
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error while processing your request. Please try again.",
                "mentioned_patients": [],
                "total_patients": 0,
                "context_method": "error"
            }
    
    def _get_all_patients(self) -> List[Dict[str, Any]]:
        """Fetch all patients from SQLite database"""
        db = SessionLocal()
        try:
            db_service = DatabaseService(db)
            patients = db_service.get_all_patients()
            
            # Convert to dict format for Gemini
            patients_data = []
            for patient in patients:
                patients_data.append({
                    "id": patient.id,
                    "name": patient.name,
                    "date_of_birth": patient.date_of_birth,
                    "diagnosis": patient.diagnosis,
                    "prescription": patient.prescription,
                    "created_at": patient.created_at.isoformat() if patient.created_at else None,
                    "updated_at": patient.updated_at.isoformat() if patient.updated_at else None
                })
            
            logger.info(f"Retrieved {len(patients_data)} patients for chat context")
            return patients_data
            
        except Exception as e:
            logger.error(f"Error fetching patients: {str(e)}")
            return []
        finally:
            db.close()
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the chat service"""
        try:
            patients_count = len(self._get_all_patients())
            return {
                "status": "healthy",
                "patients_available": patients_count,
                "service_type": "direct_gemini_chat"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service_type": "direct_gemini_chat"
            }
