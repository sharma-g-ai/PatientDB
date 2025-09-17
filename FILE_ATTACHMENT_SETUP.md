# File Attachment Chat Feature - Installation and Setup

## Backend Dependencies Installation

1. **Install Python dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Install additional dependencies if needed:**
```bash
pip install pandas openpyxl xlrd
```

## Frontend Dependencies Installation

1. **Install Lucide React icons:**
```bash
cd frontend
npm install lucide-react
```

## Features Implemented

### 🔧 Backend Features
- **Chat Context Service**: Manages chat sessions and file attachments with persistence
- **File Processing**: Supports Excel, CSV, PDF, Images, and text files
- **Pandas Integration**: Efficient tabular data processing with statistics and summaries
- **File Upload API**: Secure file upload with session management
- **Context Persistence**: Chat context persists throughout the conversation

### 🎨 Frontend Features
- **File Attachment Component**: Drag & drop and click-to-upload functionality
- **Enhanced Chat Interface**: Clean, modern chat UI with file attachment support
- **File Management**: View attached files, remove files, and see file info
- **Session Management**: Start new sessions, clear sessions
- **Real-time Updates**: Live file upload status and progress

## File Types Supported
- **📊 Tabular Data**: `.csv`, `.xlsx`, `.xls` (with pandas analysis)
- **📄 Documents**: `.pdf`, `.txt`, `.json`
- **🖼️ Images**: `.jpg`, `.jpeg`, `.png`, `.gif`

## How It Works

### File Processing Flow:
1. User selects/drags files into the chat
2. Files are uploaded to the backend via `/api/chat/upload-file`
3. Files are stored in the chat session context
4. When user sends a message, all attached files are processed:
   - **Excel/CSV**: Pandas generates statistical summaries and sample data
   - **PDF**: Gemini Vision API extracts and analyzes content
   - **Images**: Gemini Vision API describes and extracts text/data
   - **Text**: Content is directly added to context
5. Processed content is added to the conversation context
6. LLM generates response with full context awareness

### Context Persistence:
- Each chat session has a unique ID
- All messages and file attachments are stored per session
- Context summary is maintained for efficient LLM processing
- Files remain in context for the entire session

## Usage Examples

### 1. Upload a CSV file with patient data:
```
User: *uploads patients.csv*
Assistant: 📊 CSV File: patients.csv
Shape: 150 rows, 8 columns
Columns: PatientID, Name, Age, Gender, Diagnosis, Medication, DateAdmitted, Doctor

User: "How many patients have diabetes?"
Assistant: Based on the uploaded patient data, I can see 23 patients with diabetes in the dataset...
```

### 2. Upload an Excel file with lab results:
```
User: *uploads lab_results.xlsx*
Assistant: 📊 Excel File: lab_results.xlsx
Numeric Data Summary:
  Glucose: mean=110.45, std=25.67, range=(85.00, 180.00)
  Cholesterol: mean=195.23, std=40.12, range=(120.00, 280.00)

User: "What's the average glucose level?"
Assistant: The average glucose level in your lab results is 110.45 mg/dL...
```

## API Endpoints

### Chat API (`/api/chat/`)
- `POST /start-session` - Start new chat session
- `POST /upload-file` - Upload file to session
- `POST /chat` - Send message with context
- `GET /session/{session_id}/files` - Get session files
- `DELETE /session/{session_id}` - Clear session

## Security Considerations
- File size limits can be configured
- Supported file types are validated
- Temporary files are cleaned up after processing
- Session isolation prevents cross-session data access

## Next Steps
1. Install the dependencies
2. Start the backend server
3. Start the frontend
4. Navigate to the Chat page
5. Try uploading different file types and asking questions about them

The chat will now have full context awareness across all uploaded files and maintain that context throughout the conversation!