import os
from typing import Dict, List, Optional
import faiss
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class VectorStore:
    def __init__(self, max_features: int = 2048):
        """Initialize the vector store with TF-IDF vectorizer."""
        self.vectorizer = TfidfVectorizer(max_features=max_features, 
                                         ngram_range=(1, 2),  # Use both unigrams and bigrams
                                         stop_words='english')
        self.index = None
        self.texts = []
        self.metadata = []
        self.fitted = False
        
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
        
        # Create embeddings for all texts using TF-IDF
        if not self.fitted:
            embeddings = self.vectorizer.fit_transform(all_texts).toarray().astype('float32')
            self.fitted = True
        else:
            embeddings = self.vectorizer.transform(all_texts).toarray().astype('float32')
        
        # Initialize FAISS index if it doesn't exist
        if self.index is None:
            dimension = embeddings.shape[1]
            # Use L2 normalization for improved similarity results
            normalized_embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            self.index = faiss.IndexFlatIP(dimension)  # Using inner product instead of L2 distance
            self.index.add(normalized_embeddings)
        else:
            # Use L2 normalization for improved similarity results
            normalized_embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            self.index.add(normalized_embeddings)
        
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
        if not self.index or self.index.ntotal == 0 or not self.fitted:
            print("Vector store is empty or not initialized")
            return []
        
        # Enhance query with preprocessing before encoding
        enhanced_query = self._enhance_query(query)
        
        # Encode the query using the fitted vectorizer
        query_embedding = self.vectorizer.transform([enhanced_query]).toarray().astype('float32')
        
        # Normalize the query embedding
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
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
        
        # Sort by relevance score (higher is better for inner product)
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        
        return results
    
    def _enhance_query(self, query: str) -> str:
        """
        Enhance query with additional processing for better matching.
        """
        # Remove question words that might confuse the retrieval
        question_words = ["what", "how", "when", "where", "why", "who", "which"]
        query_words = query.lower().split()
        important_words = [word for word in query_words if word not in question_words]
        
        # If after filtering we still have words, use them, otherwise use original query
        if len(important_words) > 1:  # Keep at least 2 words
            enhanced_query = " ".join(important_words)
        else:
            enhanced_query = query
            
        return enhanced_query
    
    def save(self, directory: str = "models"):
        """Save the vector store to disk."""
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Save FAISS index
        index_path = os.path.join(directory, "faiss_index.bin")
        faiss.write_index(self.index, index_path)
        
        # Save texts, metadata, and vectorizer
        import pickle
        with open(os.path.join(directory, "texts_metadata.pkl"), "wb") as f:
            pickle.dump((self.texts, self.metadata), f)
            
        with open(os.path.join(directory, "vectorizer.pkl"), "wb") as f:
            pickle.dump(self.vectorizer, f)
        
        print(f"Vector store saved to {directory}")
    
    def load(self, directory: str = "models") -> bool:
        """Load the vector store from disk."""
        index_path = os.path.join(directory, "faiss_index.bin")
        metadata_path = os.path.join(directory, "texts_metadata.pkl")
        vectorizer_path = os.path.join(directory, "vectorizer.pkl")
        
        if not os.path.exists(index_path) or not os.path.exists(metadata_path) or not os.path.exists(vectorizer_path):
            print(f"Could not find saved vector store in {directory}")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(index_path)
            
            # Load texts and metadata
            import pickle
            with open(metadata_path, "rb") as f:
                self.texts, self.metadata = pickle.load(f)
                
            # Load vectorizer
            with open(vectorizer_path, "rb") as f:
                self.vectorizer = pickle.load(f)
                
            self.fitted = True
            
            print(f"Vector store loaded from {directory} with {len(self.texts)} documents")
            return True
        except Exception as e:
            print(f"Error loading vector store: {e}")
            return False
