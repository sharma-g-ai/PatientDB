# Adding File Attachment to Your Existing Chat

## 🚀 Quick Integration Steps

### 1. **Add Attachment Button to Your Current Chat Component**

In your existing chat component, add these elements:

```jsx
// Add these imports
import { Paperclip, X, FileText, Image, Table } from 'lucide-react';

// Add these state variables
const [attachedFiles, setAttachedFiles] = useState([]);
const [isUploading, setIsUploading] = useState(false);
const fileInputRef = useRef(null);

// Add this file upload handler
const handleFileSelect = async (event) => {
  const files = Array.from(event.target.files);
  if (files.length === 0) return;

  setIsUploading(true);
  
  try {
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('chat_session_id', chatSessionId);

      const response = await fetch('/api/documents/attach-to-chat', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setAttachedFiles(prev => [...prev, {
          id: Date.now() + Math.random(),
          name: file.name,
          type: file.type,
          attachmentType: result.attachment_type
        }]);
      }
    }
  } catch (error) {
    console.error('File upload error:', error);
  } finally {
    setIsUploading(false);
    event.target.value = '';
  }
};

// Add this to your input area JSX
<>
  <input
    type="file"
    ref={fileInputRef}
    onChange={handleFileSelect}
    multiple
    accept=".pdf,.jpg,.jpeg,.png,.txt,.xlsx,.xls,.csv,.tsv,.json"
    className="hidden"
  />
  
  <button
    onClick={() => fileInputRef.current?.click()}
    disabled={isUploading}
    className="flex items-center justify-center w-10 h-10 bg-green-600 hover:bg-green-700 rounded-lg"
  >
    <Paperclip className="w-5 h-5 text-white" />
  </button>
</>

// Add attached files display (before messages area)
{attachedFiles.length > 0 && (
  <div className="bg-gray-800 p-3 border-b border-gray-700">
    <div className="flex flex-wrap gap-2">
      {attachedFiles.map(file => (
        <div key={file.id} className="flex items-center gap-2 bg-gray-700 rounded px-2 py-1">
          <span className="text-sm">{file.name}</span>
          <button onClick={() => setAttachedFiles(prev => prev.filter(f => f.id !== file.id))}>
            <X className="w-3 h-3" />
          </button>
        </div>
      ))}
    </div>
  </div>
)}
```

### 2. **Test the Integration**

1. **Start your backend server**:
   ```bash
   cd backend
   python main.py
   ```

2. **Access the chat at**: `http://localhost:8000/chat`

3. **Or integrate into your React app** using the component above

### 3. **Backend is Ready**

The backend endpoints are already implemented:
- ✅ `POST /api/documents/attach-to-chat` - File upload
- ✅ `POST /api/chat/message` - Enhanced chat with context
- ✅ `GET /api/documents/chat-attachments/{session_id}` - Get attachments

### 4. **Supported File Types**

- **Documents**: PDF, Images (JPG, PNG), Text files
- **Tabular Data**: Excel (.xlsx, .xls), CSV, TSV, JSON
- **Size Limit**: 20MB per file

## 🔧 **If You Want to Use the Standalone Chat**

Simply go to `http://localhost:8000/chat` after starting your server - it should show the attachment button.

## 🎯 **Key Features**

- **📎 Paperclip Icon**: Click to attach files
- **Visual Indicators**: Shows attached files count
- **Context Awareness**: AI knows about all attached files
- **Multiple Formats**: Supports documents and tabular data
- **Real-time Updates**: Files appear immediately after upload

Let me know if you need help integrating this into your specific React component!