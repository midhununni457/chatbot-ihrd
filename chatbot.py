import os
from typing import List, Dict, Optional

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    # Add tqdm to imports to make the dependency clear
    import tqdm
except ModuleNotFoundError as e:
    module_name = str(e).split("'")[1]
    print(f"Error: Missing required module: {module_name}")
    print(f"Please install it using: pip install {module_name}")
    print("Or install all dependencies with: pip install -r requirements.txt")
    exit(1)

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
        model_dir = "models"
        
        if not force_reload and os.path.exists(model_dir):
            # Try to load existing vector store
            loaded = self.vector_store.load()
            if loaded:
                return
        
        # Process PDFs and create vector store
        document_chunks = self.pdf_processor.process_pdf_documents()
        
        if not document_chunks:
            print("No document chunks to add to vector store")
            return
            
        print("Initializing knowledge base with document chunks...")
        self.vector_store.add_texts(document_chunks)
        
        # Create models directory if it doesn't exist
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        self.vector_store.save()
        print("Knowledge base initialized successfully")
    
    def retrieve_relevant_context(self, query: str, max_chunks: int = 5) -> str:
        """Retrieve relevant context for the query from the vector store."""
        results = self.vector_store.search(query, k=max_chunks)
        
        if not results:
            return "No relevant information found."
        
        # Format context with clear document references
        context_items = []
        for i, result in enumerate(results):
            source = result["metadata"]["source"]
            text = result["text"].strip()
            score = result["score"]
            context_items.append({
                "source": source,
                "text": text,
                "score": score
            })
        
        # Sort by relevance score
        context_items = sorted(context_items, key=lambda x: x["score"], reverse=True)
        
        # Format the context
        context = ""
        for i, item in enumerate(context_items):
            context += f"\nDocument: {item['source']}\nContent: {item['text']}\n"
        
        return context
    
    def generate_response(self, query: str) -> str:
        """Generate a response to the query using RAG approach with Gemini."""
        # Retrieve relevant context
        context = self.retrieve_relevant_context(query)
        
        if "No relevant information found" in context:
            # Try a different approach - break down the query into keywords
            keywords = self._extract_keywords(query)
            if keywords:
                print(f"Trying keyword search with: {keywords}")
                context = self.retrieve_relevant_context(keywords)
        
        # Create system message with instructions
        system_message = """You are a helpful assistant answering questions based on the provided documents.
Carefully analyze the context to provide accurate answers.
If the information is present in the context, provide a detailed and helpful answer.
If the answer is not in the context, say: "I don't have enough information to answer this question."
DO NOT mention phrases like "based on the context" or "according to the documents" in your answer.
Do not make up information that is not in the provided context.
Focus on being accurate, direct, and helpful."""
        
        # Create prompt with context and query
        prompt = f"{system_message}\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": query})
        
        # Generate response using Gemini API
        try:
            # Configure generation parameters
            generation_config = {
                "temperature": 0.3,  # Lower temperature for more precise answers
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
    
    def _extract_keywords(self, query: str) -> str:
        """Extract important keywords from the query for better retrieval."""
        # Remove common question words and stopwords
        stopwords = ["a", "an", "the", "what", "how", "when", "where", "why", "who", "is", "are", "was", "were", 
                     "do", "does", "did", "has", "have", "had", "can", "could", "will", "would", "should", "may", 
                     "might", "must", "about"]
        
        words = query.lower().replace('?', '').replace('.', '').replace(',', '').split()
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        # Return the keywords joined by spaces
        return " ".join(keywords)
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        print("Conversation history reset.")
    
    def force_reload_knowledge_base(self):
        """Force reload the knowledge base."""
        self.initialize_knowledge_base(force_reload=True)
        print("Knowledge base reloaded.")
