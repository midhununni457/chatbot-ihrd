import os
import asyncio
import websockets
import json
import ssl
from aiohttp import web
from main import load_qa_pairs, chatbot_response

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

ALL_QA_PAIRS = None

PORT = int(os.environ.get("PORT", 8080))
HOST = os.environ.get("HOST", "0.0.0.0")
WS_PORT = int(os.environ.get("WS_PORT", 8081))

# Check if running on Render
IS_RENDER = os.environ.get("RENDER", "0") == "1"

SECURE = os.environ.get("SECURE", "0") == "1"

async def websocket_handler(websocket, path=None):
    global ALL_QA_PAIRS
    
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

# WebSocket handler for use with aiohttp routes
async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # Load QA pairs if not already loaded
    global ALL_QA_PAIRS
    if ALL_QA_PAIRS is None:
        ALL_QA_PAIRS = load_all_qa_pairs()
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    response = chatbot_response(msg.data, ALL_QA_PAIRS)
                    await ws.send_json({"response": response})
                except Exception:
                    await ws.send_json({"response": "Sorry, I encountered an error while processing your request."})
            elif msg.type == web.WSMsgType.ERROR:
                print(f"WebSocket connection closed with exception: {ws.exception()}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        return ws

async def run_server():
    try:
        # Set up SSL if secure connection is requested
        ssl_context = None
        if SECURE:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(
                os.environ.get("SSL_CERT", "fullchain.pem"),
                os.environ.get("SSL_KEY", "privkey.pem")
            )
        
        # Set up app with WebSocket support
        app = web.Application()
        app.add_routes([
            web.get('/', index),
            web.get('/static/css/style.css', get_style),
            web.get('/static/js/script.js', get_script),
            web.get('/ws', ws_handler),  # Add WebSocket endpoint
        ])
        
        # Start the app
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, HOST, PORT, ssl_context=ssl_context)
        await site.start()
        print(f"HTTP server started at http{'s' if SECURE else ''}://{HOST}:{PORT}")
        
        # Only start separate WebSocket server if not on Render
        if not IS_RENDER:
            ws_version = websockets.__version__.split('.')
            major_version = int(ws_version[0]) if ws_version and ws_version[0].isdigit() else 0
            
            if major_version >= 10:
                ws_server = await websockets.serve(
                    websocket_handler, 
                    HOST,
                    WS_PORT, 
                    ping_interval=30,
                    ping_timeout=10,
                    ssl=ssl_context
                )
            else:
                ws_server = await websockets.serve(
                    lambda ws, path: websocket_handler(ws, path),
                    HOST,
                    WS_PORT,
                    ping_interval=30,
                    ping_timeout=10,
                    ssl=ssl_context
                )
                
            print(f"WebSocket server started at {'wss' if SECURE else 'ws'}://{HOST}:{WS_PORT}")
        
        # Wait forever
        await asyncio.Future()
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Server error: {str(e)}")
    finally:
        if 'ws_server' in locals():
            ws_server.close()
            await ws_server.wait_closed()
        if 'runner' in locals():
            await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("Servers shut down by keyboard interrupt")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
