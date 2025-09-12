import google.generativeai as genai
import os
from typing import Dict, Any, Optional
import json
import logging
from PIL import Image
import io
import base64

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    async def extract_patient_data(self, file_content: bytes, file_type: str) -> Dict[str, Any]:
        """Extract patient data from uploaded document"""
        try:
            prompt = """
            You are a medical document processor. Extract patient information from the provided document(s).
            
            The uploaded documents may include:
            1. Patient ID documents (Aadhaar card, PAN card, or other government IDs)
            2. Medical prescriptions
            3. Medical reports or diagnoses
            
            Please extract the following information and return it in JSON format:
            {
                "name": "Patient's full name",
                "date_of_birth": "Date in YYYY-MM-DD format",
                "diagnosis": "Medical diagnosis or condition",
                "prescription": "Prescribed medications and instructions",
                "confidence_score": 0.95,
                "raw_text": "All extracted text from the document"
            }
            
            IMPORTANT EXTRACTION RULES:
            1. **Patient Identity**: If you see an Aadhaar card, PAN card, or any government ID document, extract the person's name and date of birth from these documents as they are the most reliable source for patient identity.
            
            2. **Name Extraction**: 
               - Prioritize name from ID documents (Aadhaar, PAN card)
               - If no ID document, extract from prescription header or patient details section
               - Use the full name as it appears on the official document
            
            3. **Date of Birth**: 
               - Extract DOB from ID documents first (Aadhaar cards show DOB, PAN cards show it in some cases)
               - If not available on ID, look for age or DOB mentioned in medical documents
               - Convert any date format to YYYY-MM-DD format
               - If only age is mentioned, estimate DOB based on current date
            
            4. **Diagnosis Intelligence**:
               - If diagnosis is explicitly mentioned in the document, extract it directly
               - If diagnosis is NOT clearly stated but prescription is available, analyze the prescribed medications to reverse-engineer the likely diagnosis
               - Use your medical knowledge to infer conditions from medication patterns:
                 * Antibiotics (Amoxicillin, Azithromycin) → Bacterial infections
                 * Bronchodilators (Salbutamol, Levolin) → Respiratory conditions like Asthma/COPD
                 * Antacids (Pantoprazole, Omeprazole) → Gastric issues/GERD
                 * Antidiabetic drugs (Metformin, Insulin) → Diabetes
                 * Antihypertensives (Amlodipine, Enalapril) → Hypertension
                 * Pain medications + anti-inflammatory → Musculoskeletal conditions
               - Provide the most likely diagnosis based on medication analysis
            
            5. **Prescription Processing**:
               - Extract all medications with dosage, frequency, and duration
               - Include both generic and brand names if available
               - Note any special instructions or precautions
            
            6. **Quality Assurance**:
               - If information is not clearly available, use null for that field
               - Confidence score should reflect how certain you are about the extraction (0-1)
               - Include all visible text in raw_text field for reference
               - Higher confidence for information extracted from official ID documents
            
            Document to process:
            """
            
            if file_type.startswith('image/'):
                # Process image file
                image = Image.open(io.BytesIO(file_content))
                response = await self._generate_content_with_image(prompt, image)
            else:
                # Process text file (assuming it's readable text)
                text_content = file_content.decode('utf-8', errors='ignore')
                full_prompt = f"{prompt}\n\n{text_content}"
                response = await self._generate_content_with_text(full_prompt)
            
            return self._parse_response(response)
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return {
                "name": None,
                "date_of_birth": None,
                "diagnosis": None,
                "prescription": None,
                "confidence_score": 0.0,
                "raw_text": f"Error processing document: {str(e)}"
            }
    
    async def _generate_content_with_image(self, prompt: str, image: Image.Image) -> str:
        """Generate content from image using Gemini"""
        try:
            response = self.model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            logger.error(f"Error generating content from image: {str(e)}")
            raise
    
    async def _generate_content_with_text(self, prompt: str) -> str:
        """Generate content from text using Gemini"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating content from text: {str(e)}")
            raise
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response to extract JSON data"""
        try:
            # Try to find JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback: create structured response from text
                return {
                    "name": None,
                    "date_of_birth": None,
                    "diagnosis": None,
                    "prescription": None,
                    "confidence_score": 0.5,
                    "raw_text": response
                }
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON from Gemini response")
            return {
                "name": None,
                "date_of_birth": None,
                "diagnosis": None,
                "prescription": None,
                "confidence_score": 0.3,
                "raw_text": response
            }
    
    async def generate_chat_response(self, query: str, context: str) -> str:
        """Generate chat response based on query and context"""
        prompt = f"""
        You are a helpful medical assistant. Answer the user's question based on the provided patient data context.
        
        Context (Patient Data):
        {context}
        
        User Question: {query}
        
        Please provide a helpful, accurate response based only on the information provided in the context.
        If the context doesn't contain enough information to answer the question, please say so.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request."
