import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
import numpy as np
from app.services.database_service import DatabaseService
from app.database import SessionLocal
from app.services.gemini_service import GeminiService
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="patient_data",
            metadata={"hnsw:space": "cosine"}
        )
        if SentenceTransformer is not None:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.encoder = None
            logger.warning("SentenceTransformer not available. RAG functionality will be limited.")
        self.gemini_service = GeminiService()
    
    async def add_patient_to_vector_store(self, patient_data: Dict[str, Any]):
        """Add patient data to vector store for RAG"""
        try:
            if self.encoder is None:
                logger.warning("Encoder not available, skipping vector store update")
                return
                
            # Create text representation of patient data
            text_content = self._create_patient_text(patient_data)
            
            # Generate embedding
            embedding = self.encoder.encode([text_content])[0].tolist()
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[text_content],
                metadatas=[{
                    "patient_id": patient_data["id"],
                    "name": patient_data.get("name", ""),
                    "date_of_birth": patient_data.get("date_of_birth", ""),
                    "type": "patient_record"
                }],
                ids=[f"patient_{patient_data['id']}"]
            )
            
            logger.info(f"Added patient {patient_data['id']} to vector store")
            
        except Exception as e:
            logger.error(f"Error adding patient to vector store: {str(e)}")
            raise
    
    def _create_patient_text(self, patient_data: Dict[str, Any]) -> str:
        """Create searchable text from patient data"""
        parts = []
        
        if patient_data.get("name"):
            parts.append(f"Patient Name: {patient_data['name']}")
        
        if patient_data.get("date_of_birth"):
            parts.append(f"Date of Birth: {patient_data['date_of_birth']}")
        
        if patient_data.get("diagnosis"):
            parts.append(f"Diagnosis: {patient_data['diagnosis']}")
        
        if patient_data.get("prescription"):
            parts.append(f"Prescription: {patient_data['prescription']}")
        
        return " | ".join(parts)
    
    async def search_similar_patients(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar patients based on query"""
        try:
            if self.encoder is None:
                logger.warning("Encoder not available, returning empty results")
                return []
                
            # Generate query embedding
            query_embedding = self.encoder.encode([query])[0].tolist()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results with proper null checking
            similar_patients = []
            if (results and 
                isinstance(results.get('documents'), list) and 
                len(results['documents']) > 0 and
                results['documents'][0] is not None):
                
                documents = results['documents'][0]
                metadatas = results.get('metadatas', [[]])[0] or []
                distances = results.get('distances', [[]])[0] or []
                
                for i in range(len(documents)):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    distance = distances[i] if i < len(distances) else 0.5
                    
                    similar_patients.append({
                        "content": documents[i],
                        "metadata": metadata,
                        "similarity_score": 1 - distance
                    })
            
            return similar_patients
            
        except Exception as e:
            logger.error(f"Error searching similar patients: {str(e)}")
            return []
    
    async def generate_rag_response(self, query: str) -> Dict[str, Any]:
        """Generate response using RAG (Retrieval-Augmented Generation)"""
        try:
            # Retrieve relevant patient data
            similar_patients = await self.search_similar_patients(query, top_k=5)
            
            # Create context from retrieved data
            context = "\n\n".join([
                f"Patient Record {i+1}: {patient['content']}"
                for i, patient in enumerate(similar_patients)
            ])
            
            # Generate response using Gemini
            response = await self.gemini_service.generate_chat_response(query, context)
            
            # Extract patient IDs from results
            patient_ids = [
                patient['metadata'].get('patient_id', '')
                for patient in similar_patients
                if patient['metadata'].get('patient_id')
            ]
            
            # Extract sources
            sources = [
                patient['metadata'].get('name', 'Unknown Patient')
                for patient in similar_patients
                if patient['metadata'].get('name')
            ]
            
            return {
                "response": response,
                "sources": sources,
                "patient_ids": patient_ids,
                "context_used": len(similar_patients)
            }
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error while processing your request.",
                "sources": [],
                "patient_ids": [],
                "context_used": 0
            }
    
    async def refresh_vector_store(self):
        """Refresh vector store with all patients from database"""
        try:
            # Get all patients from SQLite database
            db = SessionLocal()
            try:
                db_service = DatabaseService(db)
                patients = db_service.get_all_patients()
                
                # Clear existing collection
                try:
                    self.collection.delete()
                except:
                    pass  # Collection might not exist
                
                # Re-add all patients
                for patient in patients:
                    patient_dict = {
                        "id": patient.id,
                        "name": patient.name,
                        "date_of_birth": patient.date_of_birth,
                        "diagnosis": patient.diagnosis,
                        "prescription": patient.prescription
                    }
                    await self.add_patient_to_vector_store(patient_dict)
                
                logger.info(f"Refreshed vector store with {len(patients)} patients")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error refreshing vector store: {str(e)}")
            raise
