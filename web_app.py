import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from chatbot import RAGChatbot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize chatbot
api_key = os.getenv("GEMINI_API_KEY")
chatbot = None

def initialize_chatbot():
    global chatbot
    if not chatbot:
        chatbot = RAGChatbot(api_key=api_key)
        chatbot.initialize_knowledge_base()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/api/chat', methods=['POST'])
def chat():
    if not chatbot:
        initialize_chatbot()
    
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        response = chatbot.generate_response(query)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset():
    if chatbot:
        chatbot.reset_conversation()
    return jsonify({'status': 'Conversation reset'})

@app.route('/api/reload', methods=['POST'])
def reload_kb():
    if chatbot:
        chatbot.force_reload_knowledge_base()
        return jsonify({'status': 'Knowledge base reloaded successfully'})
    return jsonify({'error': 'Chatbot not initialized'}), 500

@app.route('/api/status', methods=['GET'])
def status():
    if not chatbot:
        initialize_chatbot()
    
    pdf_files = chatbot.pdf_processor.get_pdf_files()
    kb_status = {
        'pdf_count': len(pdf_files),
        'pdf_files': [os.path.basename(f) for f in pdf_files],
        'vector_store_initialized': chatbot.vector_store.fitted
    }
    return jsonify(kb_status)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html')

if __name__ == '__main__':
    initialize_chatbot()
    # Use PORT environment variable if available (for Render deployment)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
