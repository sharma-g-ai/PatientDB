import os
import chromadb
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        
        # Main patient collection
        self.collection = self.client.get_or_create_collection(
            name="patient_data",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Staging collection for latest uploads
        self.staging_collection = self.client.get_or_create_collection(
            name="patient_data_staging",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize Gemini for embeddings
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.embedding_model = "models/embedding-001"
        
        logger.info("RAG Service initialized with Google embeddings (no PyTorch needed)")
    
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings using Google Gemini API"""
        try:
            embeddings = []
            for text in texts:
                result = genai.embed_content(
                    model=self.embedding_model,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
            return embeddings
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            # Fallback: return dummy embeddings
            return [[0.0] * 768 for _ in texts]
    
    async def add_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add document to vector store using Google embeddings"""
        try:
            # Split content into chunks
            chunks = self._chunk_text(content)
            embeddings = self._get_embeddings(chunks)
            
            # Add to ChromaDB
            ids = [f"doc_{metadata.get('filename', 'unknown')}_{i}" for i in range(len(chunks))]
            
            self.staging_collection.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=[metadata] * len(chunks),
                ids=ids
            )
            
            return f"Added {len(chunks)} chunks to vector store"
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return f"Error: {str(e)}"
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple text chunking"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks
    
    async def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            # Get query embedding
            query_embedding = self._get_embeddings([query])[0]
            
            # Search in both collections
            results = []
            for collection in [self.collection, self.staging_collection]:
                try:
                    search_results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=n_results
                    )
                    results.extend(search_results.get('documents', [[]])[0])
                except:
                    continue
            
            return results[:n_results]
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []