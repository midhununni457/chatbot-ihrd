import os
from web_app import app, initialize_chatbot

if __name__ == "__main__":
    # Initialize the chatbot at startup
    initialize_chatbot()
    
    # Use PORT environment variable if available (for Render deployment)
    port = int(os.environ.get('PORT', 5000))
    
    # Start the Flask web server
    app.run(host='0.0.0.0', port=port, debug=True)
    
    print(f"Web interface is running at http://localhost:{port}")
