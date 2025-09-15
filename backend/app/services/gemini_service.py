import google.generativeai as genai
from google import genai as google_client
import os
from typing import Dict, Any, Optional, List
import json
import logging
from PIL import Image
import io
import base64
import mimetypes
import tempfile
import shutil
import re

logger = logging.getLogger(__name__)

# Configure logger to ensure it outputs to console
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = True

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        # Use the google.genai client for file uploads (like in main.py)
        self.client = google_client.Client(api_key=api_key)
    
    async def extract_patient_data(self, file_content: bytes, file_type: str) -> Dict[str, Any]:
        """Extract patient data from uploaded document"""
        try:
            print(f"🔍 Processing document of type: {file_type}, size: {len(file_content)} bytes")
            logger.info(f"Processing document of type: {file_type}, size: {len(file_content)} bytes")
            
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
                print("📷 Processing as image document")
                logger.info("Processing as image document")
                image = Image.open(io.BytesIO(file_content))
                response = self._generate_content_with_image(prompt, image)
            elif file_type == 'application/pdf':
                # Process PDF file - use Gemini file upload API for better PDF handling
                print("📄 Processing as PDF document using file upload API")
                logger.info("Processing as PDF document using file upload API")
                
                # Create temp file for PDF
                temp_dir = tempfile.mkdtemp()
                try:
                    pdf_path = os.path.join(temp_dir, 'document.pdf')
                    with open(pdf_path, 'wb') as f:
                        f.write(file_content)
                    
                    # Upload to Gemini - use 'file' parameter instead of 'path'
                    uploaded_file = self.client.files.upload(
                        file=pdf_path,
                        config={"mime_type": "application/pdf"}
                    )
                    
                    # Generate content using uploaded file with proper message structure
                    response = self.client.models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=[
                            {"role": "user", "parts": [
                                {"file_data": {"mime_type": uploaded_file.mime_type, "file_uri": uploaded_file.uri}},
                                {"text": prompt}
                            ]}
                        ]
                    )
                    response = response.text
                    
                finally:
                    # Clean up temp file
                    import shutil
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
            else:
                # Process text file (assuming it's readable text)
                print("📄 Processing as text document")
                logger.info("Processing as text document")
                try:
                    text_content = file_content.decode('utf-8', errors='ignore')
                except UnicodeDecodeError:
                    # If UTF-8 fails, try other common encodings
                    try:
                        text_content = file_content.decode('latin-1', errors='ignore')
                    except:
                        text_content = str(file_content, errors='ignore')
                
                full_prompt = f"{prompt}\n\n{text_content}"
                print(f"📝 Text content length: {len(text_content)} characters")
                logger.info(f"Text content length: {len(text_content)} characters")
                response = self._generate_content_with_text(full_prompt)
            
            print("=== 🤖 FULL LLM RESPONSE ===")
            print(response)
            print("=== 🏁 END LLM RESPONSE ===")
            logger.info("=== FULL LLM RESPONSE ===")
            logger.info(response)
            logger.info("=== END LLM RESPONSE ===")
            
            parsed_data = self._parse_response(response)
            print(f"✅ Parsed patient data: {parsed_data}")
            logger.info(f"Parsed patient data: {parsed_data}")
            
            return parsed_data
            
        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            logger.error(f"Error processing document: {str(e)}")
            return {
                "name": None,
                "date_of_birth": None,
                "diagnosis": None,
                "prescription": None,
                "confidence_score": 0.0,
                "raw_text": f"Error processing document: {str(e)}"
            }

    async def extract_patient_data_from_multiple_files(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract patient data from multiple uploaded documents using Gemini file upload API"""
        print(f"📁 Processing {len(files_data)} documents using Gemini file upload API")
        logger.info(f"Processing {len(files_data)} documents using Gemini file upload API")
        
        # Create temporary directory for files
        temp_dir = tempfile.mkdtemp()
        uploaded_files = []
        
        try:
            # Save files to temp directory and upload to Gemini
            for i, file_data in enumerate(files_data):
                print(f"📄 Processing document {i+1}/{len(files_data)}")
                
                file_content = file_data['content']
                file_name = file_data.get('name', f'document_{i+1}')
                file_type = file_data.get('type', 'application/octet-stream')
                
                # Determine proper MIME type
                if file_name.lower().endswith('.pdf'):
                    mime_type = 'application/pdf'
                elif file_name.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = 'image/jpeg'
                elif file_name.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif file_name.lower().endswith('.tiff'):
                    mime_type = 'image/tiff'
                else:
                    # Try to guess from provided file_type
                    mime_type = file_type if file_type != 'application/octet-stream' else 'application/pdf'
                
                print(f"� File: {file_name}, MIME type: {mime_type}")
                
                # Save file temporarily
                file_path = os.path.join(temp_dir, file_name)
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                
                # Upload to Gemini
                print(f"🔄 Uploading {file_name} to Gemini...")
                try:
                    uploaded_file = self.client.files.upload(
                        file=file_path, 
                        config={"mime_type": mime_type}
                    )
                    uploaded_files.append(uploaded_file)
                    print(f"✅ Successfully uploaded {file_name}")
                except Exception as upload_error:
                    print(f"❌ Error uploading {file_name}: {str(upload_error)}")
                    logger.error(f"Error uploading {file_name}: {str(upload_error)}")
            
            if not uploaded_files:
                raise Exception("No files were successfully uploaded to Gemini")
            
            # Create comprehensive prompt for medical document processing
            prompt = """
            You are a medical document processor. Extract patient information from the provided document(s).
            
            The uploaded documents may include:
            1. Patient ID documents (Aadhaar card, PAN card, or other government IDs)
            2. Medical prescriptions
            3. Medical reports or diagnoses
            4. Medical test results
            5. Insurance documents
            
            Please extract the following information and return it in JSON format:
            {
                "name": "Patient's full name",
                "date_of_birth": "Date in YYYY-MM-DD format",
                "diagnosis": "Medical diagnosis or condition",
                "prescription": "Prescribed medications and instructions",
                "confidence_score": 0.95,
                "raw_text": "All extracted text from all documents combined",
                "document_types": ["list of document types identified"],
                "medical_history": "Any relevant medical history mentioned",
                "doctor_name": "Name of prescribing doctor if available",
                "hospital_clinic": "Name of hospital or clinic if available"
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
            
            4. **Cross-Document Verification**:
               - If multiple documents contain the same information, use the most reliable source
               - ID documents are more reliable than medical documents for personal information
               - Medical documents are more reliable for medical information
            
            5. **Diagnosis Intelligence**:
               - If diagnosis is explicitly mentioned in any document, extract it directly
               - If diagnosis is NOT clearly stated but prescription is available, analyze the prescribed medications to reverse-engineer the likely diagnosis
               - Use your medical knowledge to infer conditions from medication patterns:
                 * Antibiotics (Amoxicillin, Azithromycin) → Bacterial infections
                 * Bronchodilators (Salbutamol, Levolin) → Respiratory conditions like Asthma/COPD
                 * Antacids (Pantoprazole, Omeprazole) → Gastric issues/GERD
                 * Antidiabetic drugs (Metformin, Insulin) → Diabetes
                 * Antihypertensives (Amlodipine, Enalapril) → Hypertension
                 * Pain medications + anti-inflammatory → Musculoskeletal conditions
               - Provide the most likely diagnosis based on medication analysis
            
            6. **Prescription Processing**:
               - Extract all medications with dosage, frequency, and duration from all documents
               - Include both generic and brand names if available
               - Note any special instructions or precautions
               - Combine prescriptions from multiple documents if present
            
            7. **Quality Assurance**:
               - If information is not clearly available, use null for that field
               - Confidence score should reflect how certain you are about the extraction (0-1)
               - Include all visible text from all documents in raw_text field for reference
               - Higher confidence for information extracted from official ID documents
            
            Process ALL the provided documents comprehensively and extract information from each one.
            """
            
            print("=== 🤖 SENDING MULTIPLE FILES TO LLM ===")
            print(f"Number of files uploaded: {len(uploaded_files)}")
            logger.info(f"Sending {len(uploaded_files)} files to Gemini for processing")
            
            # Generate content using all uploaded files with proper message structure
            user_parts = []
            for uploaded_file in uploaded_files:
                user_parts.append({
                    "file_data": {
                        "mime_type": uploaded_file.mime_type, 
                        "file_uri": uploaded_file.uri
                    }
                })
            user_parts.append({"text": prompt})
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    {"role": "user", "parts": user_parts}
                ]
            )
            
            response_text = response.text
            print("=== 🤖 FULL LLM RESPONSE ===")
            print(response_text)
            print("=== 🏁 END LLM RESPONSE ===")
            logger.info("=== FULL LLM RESPONSE ===")
            logger.info(response_text)
            logger.info("=== END LLM RESPONSE ===")
            
            parsed_data = self._parse_response(response_text)
            parsed_data["documents_processed"] = len(files_data)
            parsed_data["processing_method"] = "gemini_file_upload_api"
            
            print(f"✅ Parsed patient data from {len(files_data)} documents: {parsed_data}")
            logger.info(f"Parsed patient data from {len(files_data)} documents")
            
            return parsed_data
            
        except Exception as e:
            print(f"❌ Error processing multiple documents: {str(e)}")
            logger.error(f"Error processing multiple documents: {str(e)}")
            return {
                "name": None,
                "date_of_birth": None,
                "diagnosis": None,
                "prescription": None,
                "confidence_score": 0.0,
                "raw_text": f"Error processing documents: {str(e)}",
                "documents_processed": len(files_data),
                "processing_method": "gemini_file_upload_api"
            }
        finally:
            # Clean up temporary files
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _generate_content_with_image(self, prompt: str, image: Image.Image) -> str:
        """Generate content from image using Gemini"""
        try:
            print("=== 🤖 SENDING TO LLM (IMAGE) ===")
            print(f"Image size: {image.size}")
            print("=== 📨 END PROMPT ===")
            logger.info("=== SENDING TO LLM (IMAGE) ===")
            logger.info(f"Image size: {image.size}")
            logger.info("=== END PROMPT ===")
            
            response = self.model.generate_content([prompt, image])
            print(f"🤖 Raw Gemini response from image: {response.text}")
            logger.info(f"Raw Gemini response from image: {response.text}")
            return response.text
        except Exception as e:
            print(f"❌ Error generating content from image: {str(e)}")
            logger.error(f"Error generating content from image: {str(e)}")
            raise
    
    def _generate_content_with_text(self, prompt: str) -> str:
        """Generate content from text using Gemini"""
        try:
            print("=== 🤖 SENDING TO LLM (TEXT) ===")
            print(f"Prompt length: {len(prompt)} characters")
            print("=== 📨 END PROMPT ===")
            logger.info("=== SENDING TO LLM (TEXT) ===")
            logger.info(f"Full prompt: {prompt}")
            logger.info("=== END PROMPT ===")
            
            response = self.model.generate_content(prompt)
            print(f"🤖 Raw Gemini response from text: {response.text}")
            logger.info(f"Raw Gemini response from text: {response.text}")
            return response.text
        except Exception as e:
            print(f"❌ Error generating content from text: {str(e)}")
            logger.error(f"Error generating content from text: {str(e)}")
            raise
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response to extract JSON data"""
        def _clean_json_text(text: str) -> str:
            # Strip surrounding code fences if present
            fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
            if fenced:
                text = fenced.group(1)
            # Extract the first {...} block if still mixed content
            brace_match = re.search(r"\{[\s\S]*\}", text)
            if brace_match:
                text = brace_match.group(0)
            # Normalize smart quotes to ASCII
            replacements = {
                '\u201c': '"', '\u201d': '"', '\u201e': '"', '\u201f': '"',
                '\u2018': "'", '\u2019': "'", '\u2032': "'", '\u2033': '"'
            }
            for src, dst in replacements.items():
                text = text.replace(src, dst)
            # Remove trailing commas before } or ]
            text = re.sub(r",\s*(\}|\])", r"\1", text)
            # Remove non-printable control chars except tab/newline/carriage-return
            text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
            return text.strip()

        # Try multiple parsing strategies
        candidates: List[str] = []
        candidates.append(_clean_json_text(response))
        # If the response begins with a fence, also try raw without cleaning braces
        if response.strip().startswith("```"):
            candidates.append(response.strip().strip("`"))
        # Last resort: simple substring between first and last brace without other cleaning
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            candidates.append(response[start_idx:end_idx])

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                return parsed
            except Exception:
                continue

        logger.warning("Could not parse JSON from Gemini response")
        return {
            "name": None,
            "date_of_birth": None,
            "diagnosis": None,
            "prescription": None,
            "confidence_score": 0.3,
            "raw_text": response
        }
    
    async def generate_chat_response(self, query: str, patients_data: list) -> dict:
        """Generate chat response with direct patient data context"""
        
        # Format all patient data intelligently
        context = self._format_patients_context(patients_data)
        
        prompt = f"""
        You are an intelligent medical assistant with access to a comprehensive patient database. 
        Answer the user's question based on the provided patient records.

        PATIENT DATABASE:
        {context}

        USER QUESTION: {query}

        INSTRUCTIONS:
        1. Provide accurate, helpful responses based ONLY on the patient data provided
        2. If asked about specific patients, reference them by name and ID
        3. For statistical queries, analyze the data and provide counts/percentages
        4. If the data doesn't contain enough information, clearly state what's missing
        5. Always be professional and maintain patient confidentiality in your responses
        6. When referencing patients, include relevant details like diagnosis, prescription, etc.

        RESPONSE FORMAT:
        - Give a direct answer to the question
        - Include specific patient names/IDs when relevant
        - Provide supporting data/statistics when applicable
        - Suggest follow-up questions if appropriate
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract mentioned patients from the query and response
            mentioned_patients = self._extract_mentioned_patients(query, patients_data)
            
            return {
                "response": response.text,
                "mentioned_patients": mentioned_patients,
                "total_patients_in_context": len(patients_data)
            }
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error while processing your request. Please try again.",
                "mentioned_patients": [],
                "total_patients_in_context": 0
            }
    
    def _format_patients_context(self, patients_data: list) -> str:
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
    
    def _extract_mentioned_patients(self, query: str, patients_data: list) -> list:
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
