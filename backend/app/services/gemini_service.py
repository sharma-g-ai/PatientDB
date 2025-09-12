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
            You are a medical document processor. Extract patient information from the provided document.
            
            Please extract the following information and return it in JSON format:
            {
                "name": "Patient's full name",
                "date_of_birth": "Date in YYYY-MM-DD format",
                "diagnosis": "Medical diagnosis or condition",
                "prescription": "Prescribed medications and instructions",
                "confidence_score": 0.95,
                "raw_text": "All extracted text from the document"
            }
            
            Rules:
            1. If information is not clearly available, use null for that field
            2. For date_of_birth, convert any date format to YYYY-MM-DD
            3. Be as accurate as possible with medical terminology
            4. Confidence score should reflect how certain you are about the extraction (0-1)
            5. Include all visible text in raw_text field
            
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
