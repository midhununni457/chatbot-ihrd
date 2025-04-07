import os
from typing import List, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

from pdf_processor import PDFProcessor
from vector_store import VectorStore

# Load environment variables
load_dotenv()

class RAGChatbot:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "models/gemini-1.5-flash-latest"):
        """Initialize the RAG chatbot with Gemini API."""
        # Set Gemini API key
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set it as an environment variable GEMINI_API_KEY or pass it as a parameter.")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        
        # Initialize components for document processing and retrieval
        self.pdf_processor = PDFProcessor()
        self.vector_store = VectorStore()
        
        # Initialize conversation history
        self.conversation_history = []
        
        print(f"Initialized chatbot with {self.model_name} model")
    
    def initialize_knowledge_base(self, force_reload: bool = False):
        """
        Initialize the knowledge base by processing PDFs and creating vector store.
        If force_reload is False, it will try to load existing vector store.
        """
        if not force_reload and os.path.exists("models"):
            # Try to load existing vector store
            loaded = self.vector_store.load()
            if loaded:
                return
        
        # Process PDFs and create vector store
        document_chunks = self.pdf_processor.process_pdf_documents()
        if document_chunks:
            self.vector_store.add_texts(document_chunks)
            self.vector_store.save()
        else:
            print("No document chunks to add to vector store")
    
    def retrieve_relevant_context(self, query: str, max_chunks: int = 3) -> str:
        """Retrieve relevant context for the query from the vector store."""
        results = self.vector_store.search(query, k=max_chunks)
        
        if not results:
            return "No relevant information found."
        
        context = ""
        for i, result in enumerate(results):
            source = result["metadata"]["source"]
            text = result["text"]
            context += f"\n[Document: {source}]\n{text}\n"
        
        return context
    
    def generate_response(self, query: str) -> str:
        """Generate a response to the query using RAG approach with Gemini."""
        # Retrieve relevant context
        context = self.retrieve_relevant_context(query)
        
        # Create system message with instructions
        system_message = """You are a helpful assistant that answers questions directly and concisely.
Answer the question based on the provided context, but DO NOT mention the context or cite any sources in your answer.
If the answer is not in the context, simply say "I don't have enough information to answer this question."
Keep your answers clear, direct and to the point."""
        
        # Create prompt with context and query
        prompt = f"{system_message}\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": prompt})
        
        # Generate response using Gemini API
        try:
            # Configure generation parameters
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 800,
            }
            
            # Initialize model and generate response
            model = genai.GenerativeModel(model_name=self.model_name)
            response = model.generate_content(prompt, generation_config=generation_config)
            
            # Extract text from response
            if response and hasattr(response, 'text'):
                answer = response.text
            else:
                answer = "Failed to generate a response."
            
            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            # Keep conversation history manageable (last 6 exchanges)
            if len(self.conversation_history) > 12:
                self.conversation_history = self.conversation_history[-12:]
                
            return answer
            
        except Exception as e:
            return f"Error generating response: {e}"
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        print("Conversation history reset.")
