import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RAGService:
    """Minimal RAG service without ChromaDB/sentence-transformers dependencies"""
    
    def __init__(self):
        # Simple in-memory storage for chat attachments
        self.chat_attachments = {}
        self.staging_documents = {}
        logger.info("RAG Service initialized in minimal mode (no vector database)")
    
    async def add_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add document to simple storage"""
        try:
            doc_id = metadata.get('filename', 'unknown')
            self.staging_documents[doc_id] = {
                'content': content,
                'metadata': metadata
            }
            return f"Added document {doc_id} to simple storage"
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return f"Error: {str(e)}"
    
    async def add_staging_documents(self, upload_batch_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """Add staging documents to simple storage"""
        try:
            self.staging_documents[upload_batch_id] = {
                'content': text,
                'metadata': metadata
            }
            return f"Added staging documents for batch {upload_batch_id}"
        except Exception as e:
            logger.error(f"Error adding staging documents: {e}")
            return f"Error: {str(e)}"
    
    async def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Simple text search without vector similarity"""
        try:
            results = []
            query_lower = query.lower()
            
            # Simple keyword matching
            for doc_id, doc_data in self.staging_documents.items():
                content = doc_data.get('content', '').lower()
                if any(word in content for word in query_lower.split()):
                    results.append({
                        'content': doc_data.get('content', ''),
                        'metadata': doc_data.get('metadata', {}),
                        'score': 0.5  # Simple placeholder score
                    })
            
            return results[:n_results]
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Synchronous version of search"""
        try:
            results = []
            query_lower = query.lower()
            
            for doc_id, doc_data in self.staging_documents.items():
                content = doc_data.get('content', '').lower()
                if any(word in content for word in query_lower.split()):
                    results.append({
                        'content': doc_data.get('content', ''),
                        'metadata': doc_data.get('metadata', {}),
                        'relevance_score': 0.5
                    })
            
            return results[:k]
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    async def add_chat_attachment(self, chat_session_id: str, content: str, metadata: Dict[str, Any]):
        """Add attachment to chat session"""
        if chat_session_id not in self.chat_attachments:
            self.chat_attachments[chat_session_id] = []
        
        self.chat_attachments[chat_session_id].append({
            'content': content,
            'metadata': metadata,
            'timestamp': __import__('time').time()
        })
    
    async def get_chat_attachments(self, chat_session_id: str) -> List[Dict[str, Any]]:
        """Get attachments for a chat session"""
        return self.chat_attachments.get(chat_session_id, [])
    
    def get_chat_context(self, chat_session_id: str) -> str:
        """Get chat context from attachments"""
        attachments = self.chat_attachments.get(chat_session_id, [])
        if not attachments:
            return ""
        
        context_parts = []
        for attachment in attachments:
            content = attachment.get('content', '')
            if content:
                context_parts.append(content)
        
        return "\n\n".join(context_parts)