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
            
            # Format patient data as context string
            context = self._format_patients_context(patients_data)
            
            # Generate response using Gemini with full context
            response_text = await self.gemini_service.generate_chat_response(query, context)
            
            # Extract mentioned patients from the query
            mentioned_patients = self._extract_mentioned_patients(query, patients_data)
            
            return {
                "response": response_text,
                "mentioned_patients": mentioned_patients,
                "total_patients": len(patients_data),
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
    
    def _format_patients_context(self, patients_data: List[Dict[str, Any]]) -> str:
        """Format patient data for optimal Gemini context"""
        if not patients_data:
            return "No patient records available."
        
        formatted_context = []
        formatted_context.append(f"=== PATIENT DATABASE ({len(patients_data)} records) ===\n")
        
        for i, patient in enumerate(patients_data, 1):
            patient_info = f"""
PATIENT {i}:
- ID: {patient.get('id', 'N/A')}
- Name: {patient.get('name', 'Unknown')}
- Date of Birth: {patient.get('date_of_birth', 'N/A')}
- Diagnosis: {patient.get('diagnosis', 'Not specified')}
- Prescription: {patient.get('prescription', 'Not specified')}
- Record Created: {patient.get('created_at', 'N/A')}
---"""
            formatted_context.append(patient_info)
        
        return "\n".join(formatted_context)
    
    def _extract_mentioned_patients(self, query: str, patients_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract patients that might be relevant to the query"""
        mentioned = []
        query_lower = query.lower()
        
        for patient in patients_data:
            # Check if patient name is mentioned in query
            if patient.get('name') and patient['name'].lower() in query_lower:
                mentioned.append({
                    "id": patient.get('id'),
                    "name": patient.get('name'),
                    "reason": "name_mentioned"
                })
            # Check if diagnosis is mentioned
            elif patient.get('diagnosis') and any(
                word in patient['diagnosis'].lower() 
                for word in query_lower.split()
                if len(word) > 3
            ):
                mentioned.append({
                    "id": patient.get('id'),
                    "name": patient.get('name'),
                    "reason": "diagnosis_match"
                })
        
        return mentioned
    
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
