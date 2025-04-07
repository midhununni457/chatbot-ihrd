# PDF-based RAG Chatbot

A command-line chatbot that answers questions based on PDF documents using Retrieval-Augmented Generation (RAG) with Google's Gemini API.

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
6. Run the chatbot:
   ```
   python main.py
   ```

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
   - The response cites the source document where appropriate

## Usage

### Running the Chatbot

Run the chatbot with default settings:

```
python main.py
```

### Command Line Options

The chatbot supports several command line options:

```
python main.py --reload        # Force reload PDFs and rebuild knowledge base
python main.py --model MODEL   # Specify the Gemini model (default: models/gemini-1.5-flash-latest)
python main.py --timeout SECS  # Set response timeout in seconds (default: 60)
```

### Available Commands

Once the chatbot is running, you can use these commands:

- Type your question and press Enter to get a response
- Type `clear` or `reset` to clear conversation history
- Type `exit`, `quit`, or `q` to exit the chatbot

### Downloading Models

If you want to use a local LLM model instead of Gemini API:

```
python download_model.py       # Download recommended model based on your system
python download_model.py --model tiny|small|medium|large  # Specify model size
```

After downloading, update your `.env` file to use the local model by setting:

```
MODEL_PROVIDER=local
```
