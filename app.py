import os
import asyncio
import websockets
import json
from aiohttp import web
from main import load_qa_pairs, chatbot_response

# Get all QA pairs from all files in the processed directory
def load_all_qa_pairs():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    processed_dir = os.path.join(script_dir, "data", "processed")
    
    all_qa_pairs = {}
    for filename in os.listdir(processed_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(processed_dir, filename)
            try:
                qa_pairs = load_qa_pairs(file_path)
                all_qa_pairs.update(qa_pairs)
            except Exception:
                pass
    
    return all_qa_pairs

# Global QA pairs to avoid reloading for every connection
ALL_QA_PAIRS = None

# WebSocket handler
async def websocket_handler(websocket, path=None):
    global ALL_QA_PAIRS
    
    # Load QA pairs once if not already loaded
    if ALL_QA_PAIRS is None:
        ALL_QA_PAIRS = load_all_qa_pairs()
    
    try:
        async for message in websocket:
            try:
                response = chatbot_response(message, ALL_QA_PAIRS)
                await websocket.send(json.dumps({"response": response}))
            except Exception:
                await websocket.send(json.dumps({"response": "Sorry, I encountered an error while processing your request."}))
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception:
        pass

# HTTP route handlers
async def index(request):
    try:
        with open(os.path.join(os.path.dirname(__file__), 'templates', 'index.html'), 'r', encoding='utf-8') as file:
            content = file.read()
        return web.Response(text=content, content_type='text/html')
    except Exception as e:
        return web.Response(text=f"Error: {str(e)}", status=500)

async def get_style(request):
    try:
        with open(os.path.join(os.path.dirname(__file__), 'static', 'css', 'style.css'), 'r', encoding='utf-8') as file:
            content = file.read()
        return web.Response(text=content, content_type='text/css')
    except Exception:
        return web.Response(text="", status=404)

async def get_script(request):
    try:
        with open(os.path.join(os.path.dirname(__file__), 'static', 'js', 'script.js'), 'r', encoding='utf-8') as file:
            content = file.read()
        return web.Response(text=content, content_type='text/javascript')
    except Exception:
        return web.Response(text="", status=404)

# Main function to run both WebSocket and HTTP servers
async def run_server():
    # WebSocket server
    try:
        # Check WebSockets version to handle API differences
        ws_version = websockets.__version__.split('.')
        major_version = int(ws_version[0]) if ws_version and ws_version[0].isdigit() else 0
        
        if major_version >= 10:
            # New API (10.0+)
            ws_server = await websockets.serve(
                websocket_handler, 
                "0.0.0.0",
                8765, 
                ping_interval=30,
                ping_timeout=10
            )
        else:
            # Legacy API
            ws_server = await websockets.serve(
                lambda ws, path: websocket_handler(ws, path),
                "0.0.0.0",
                8765,
                ping_interval=30,
                ping_timeout=10
            )
            
        print("WebSocket server started at ws://0.0.0.0:8765")
    except Exception as e:
        print(f"Failed to start WebSocket server: {str(e)}")
        return
    
    # HTTP server
    try:
        app = web.Application()
        app.add_routes([
            web.get('/', index),
            web.get('/static/css/style.css', get_style),
            web.get('/static/js/script.js', get_script),
        ])
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        print("HTTP server started at http://0.0.0.0:8080")
    except Exception as e:
        print(f"Failed to start HTTP server: {str(e)}")
        return
    
    # Keep the server running
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass
    finally:
        ws_server.close()
        await ws_server.wait_closed()
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("Servers shut down by keyboard interrupt")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
