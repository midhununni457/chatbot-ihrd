import os
from typing import Dict, List, Optional
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the vector store with the specified embedding model."""
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.texts = []
        self.metadata = []
        
    def add_texts(self, document_chunks: Dict[str, List[str]]):
        """
        Add document chunks to the vector store.
        
        Args:
            document_chunks: Dictionary mapping document names to lists of text chunks
        """
        all_texts = []
        all_metadata = []
        
        for doc_name, chunks in document_chunks.items():
            for i, chunk in enumerate(chunks):
                all_texts.append(chunk)
                all_metadata.append({"source": doc_name, "chunk_id": i})
        
        # Create embeddings for all texts
        embeddings = self.model.encode(all_texts)
        
        # Initialize FAISS index if it doesn't exist
        if self.index is None:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
        
        # Add embeddings to the index
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Store texts and metadata
        self.texts.extend(all_texts)
        self.metadata.extend(all_metadata)
        
        print(f"Added {len(all_texts)} text chunks to the vector store")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for similar texts to the query.
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            List of dictionaries containing text and metadata
        """
        if not self.index or self.index.ntotal == 0:
            print("Vector store is empty")
            return []
        
        # Encode the query
        query_embedding = self.model.encode([query])[0].reshape(1, -1).astype('float32')
        
        # Search the index
        distances, indices = self.index.search(query_embedding, k=min(k, len(self.texts)))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.texts) and idx >= 0:
                results.append({
                    "text": self.texts[idx],
                    "metadata": self.metadata[idx],
                    "score": float(distances[0][i])
                })
        
        return results
    
    def save(self, directory: str = "models"):
        """Save the vector store to disk."""
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        index_path = os.path.join(directory, "faiss_index.bin")
        faiss.write_index(self.index, index_path)
        
        # Save texts and metadata
        import pickle
        with open(os.path.join(directory, "texts_metadata.pkl"), "wb") as f:
            pickle.dump((self.texts, self.metadata), f)
        
        print(f"Vector store saved to {directory}")
    
    def load(self, directory: str = "models") -> bool:
        """Load the vector store from disk."""
        index_path = os.path.join(directory, "faiss_index.bin")
        metadata_path = os.path.join(directory, "texts_metadata.pkl")
        
        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            print(f"Could not find saved vector store in {directory}")
            return False
        
        try:
            self.index = faiss.read_index(index_path)
            
            import pickle
            with open(metadata_path, "rb") as f:
                self.texts, self.metadata = pickle.load(f)
            
            print(f"Vector store loaded from {directory} with {len(self.texts)} documents")
            return True
        except Exception as e:
            print(f"Error loading vector store: {e}")
            return False
