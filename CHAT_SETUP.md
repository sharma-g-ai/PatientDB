# Enhanced Chat with File Attachments - Setup Instructions

## 🔧 Installation Steps

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Optional: Install PandasAI for Advanced Tabular Analysis**:
   ```bash
   pip install pandasai
   ```

3. **Environment Setup**:
   Add to your `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   MAX_CHAT_FILE_SIZE=20971520  # 20MB max for chat attachments
   ```

4. **Start the Server**:
   ```bash
   cd backend
   python main.py
   ```

5. **Access Chat Interface**:
   Open your browser and go to: `http://localhost:8000/chat`

## 🚀 New Features Added

### 1. Separate Context Management
- **Attached Files Context**: Files attached to chat sessions (primary context)
- **RAG Database Context**: Stored patient documents (secondary, optional)
- **No Context Mixing**: Attached files don't interfere with database retrievals

### 2. Chat Interface with Attach Button
- **📎 Attach Button**: Click to attach files directly in chat
- **Visual Indicators**: Shows attached files and context status  
- **Real-time Updates**: Immediate feedback on file uploads
- **Multiple File Support**: Attach multiple files in one go

### 3. File Support
- **Documents**: PDF, Images (JPG, PNG), Text files
- **Tabular Data**: Excel (.xlsx, .xls), CSV, TSV, JSON
- **Size Limit**: 20MB per file for chat attachments

## 📋 Usage Examples

### Chat Interface Usage:
1. **Open Chat**: Go to `http://localhost:8000/chat`
2. **Attach Files**: Click the 📎 button to attach files
3. **Ask Questions**: Ask about the attached files
4. **Context Awareness**: The AI remembers all attached files in the session

### API Usage:

#### Attach File to Chat:
```bash
curl -X POST "http://localhost:8000/api/documents/attach-to-chat" \
  -F "file=@patient_data.xlsx" \
  -F "chat_session_id=your-session-id"
```

#### Send Chat Message:
```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze the patient demographics in the uploaded data",
    "chat_session_id": "your-session-id"
  }'
```

#### Get Session Context:
```bash
curl "http://localhost:8000/api/chat/session/your-session-id/context"
```

## 🔥 Key Improvements

### ✅ **Context Separation**:
- Attached files have their own context space
- Database documents don't interfere with chat attachments
- Clear separation between session files and stored documents

### ✅ **User-Friendly Interface**:
- Intuitive attach button in chat
- Visual feedback for uploads
- File list display with type indicators
- Context status indicators

### ✅ **Enhanced File Processing**:
- Tabular data analysis with pandas
- Medical data detection in spreadsheets  
- Multi-format document support
- Automatic content extraction

## 🏗️ Architecture

```
Chat Session
├── Attached Files Context (Primary)
│   ├── File 1: Excel analysis
│   ├── File 2: PDF content  
│   └── File 3: Image text
│
└── Message History
    ├── User questions
    └── AI responses (with file context)

RAG Database (Separate)
├── Stored patient documents
└── General medical knowledge
```

## 🎯 Benefits

1. **No Context Pollution**: Attached files stay in their session
2. **Persistent Context**: Files remain available throughout chat
3. **Multi-Format Support**: Handle any medical document type
4. **Easy Integration**: Simple attach button interface
5. **Clear Separation**: Database vs. attached file contexts

This implementation provides clean separation between attached files and stored documents, ensuring users get exactly the context they expect!