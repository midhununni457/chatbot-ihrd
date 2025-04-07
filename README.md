# PDF-based RAG Chatbot (Web Application)

A web-based chatbot that answers questions based on PDF documents using Retrieval-Augmented Generation (RAG) with Google's Gemini API.

## Setup

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your Gemini API key:
   ```
   cp .env.example .env
   # Edit .env and add your Gemini API key
   ```
   You can obtain a Gemini API key from https://ai.google.dev/
5. Place your PDF documents in the `data` folder
6. Run the web application:
   ```
   python run_webapp.py
   ```
7. Open your browser and navigate to: http://localhost:5000

## How the RAG Process Works

The chatbot uses a Retrieval-Augmented Generation (RAG) approach, which consists of these key steps:

1. **Document Processing**:

   - PDF documents in the `data` folder are processed and text is extracted
   - Text is split into smaller chunks for efficient retrieval
   - Each chunk is associated with its source document

2. **Vector Embedding**:

   - Text chunks are converted to numerical vectors using the Sentence Transformer model
   - These vectors capture the semantic meaning of the text
   - The vectors are stored in a FAISS index for efficient similarity search

3. **Retrieval Process**:

   - When a user asks a question, it's converted to the same vector space
   - The system finds the most similar text chunks using vector similarity search
   - The top matching chunks become the "context" for answering the question

4. **Generation with Gemini**:
   - The retrieved context and user's question are sent to Google's Gemini API
   - Gemini generates a natural language response based on the given context
   - The response is displayed to the user in the web interface

## Deployment

This application is configured for easy deployment on Render.com:

1. Push your code to a Git repository
2. In Render, create a new Web Service linked to your repository
3. Render will automatically detect the configuration in `render.yaml`
4. Add your Gemini API key as an environment variable in the Render dashboard

## Environment Variables

Configure these variables in your `.env` file:

```
# Required: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Configure model
MODEL_NAME=models/gemini-1.5-flash-latest
```
