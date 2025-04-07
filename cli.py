import os
import argparse
import time
import threading
import itertools
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.text import Text
from rich import print as rprint
from dotenv import load_dotenv

from chatbot import RAGChatbot

# Load environment variables from .env file
load_dotenv()

# Global flag for response timeout
response_received = False

def main():
    """Main function to run the CLI interface."""
    console = Console()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PDF-based RAG Chatbot with Gemini API")
    parser.add_argument("--reload", action="store_true", help="Force reload PDFs and rebuild knowledge base")
    parser.add_argument("--model", type=str, default="models/gemini-1.5-flash-latest", help="Gemini model name (default: models/gemini-1.5-flash-latest)")
    parser.add_argument("--timeout", type=int, default=60, help="Response timeout in seconds (default: 60)")
    args = parser.parse_args()
    
    # Get Gemini API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]Error: GEMINI_API_KEY not found in environment variables or .env file[/bold red]")
        console.print("[yellow]Please set your Gemini API key in the .env file[/yellow]")
        return
    
    # Fancy welcome message
    console.print(Panel.fit(
        "[bold blue]PDF-based RAG Chatbot[/bold blue]\n"
        "[cyan]Ask questions about the documents in the data directory[/cyan]\n"
        f"[green]Using Google Gemini {args.model} model[/green]"
    ))
    
    try:
        # Initialize chatbot
        chatbot = RAGChatbot(api_key=api_key, model_name=args.model)
        
        # Show loading message
        with console.status("[bold green]Initializing knowledge base...[/bold green]"):
            chatbot.initialize_knowledge_base(force_reload=args.reload)
        
        console.print("\n[bold green]Ready! Type your questions or type 'exit' to quit.[/bold green]")
        console.print("[dim]Type 'clear' or 'reset' to reset conversation history[/dim]")
        
        # Main chat loop
        while True:
            query = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            query = query.strip()
            
            if query.lower() in ["exit", "quit", "bye", "q"]:
                console.print("[yellow]Goodbye![/yellow]")
                break
                
            if query.lower() in ["clear", "reset"]:
                chatbot.reset_conversation()
                console.print("[yellow]Conversation reset.[/yellow]")
                continue
                
            if not query:
                continue
            
            # Get response from chatbot with timeout handling
            global response_received
            response_received = False
            response = ["I'm still thinking..."]
            
            # Create a thread for the chatbot response
            def get_response():
                global response_received
                try:
                    result = chatbot.generate_response(query)
                    response[0] = result
                    response_received = True
                except Exception as e:
                    response[0] = f"Error generating response: {e}"
                    response_received = True
                    
            response_thread = threading.Thread(target=get_response)
            response_thread.daemon = True
            response_thread.start()
            
            # Simple spinner animation
            spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            spinner_iter = itertools.cycle(spinner_chars)
            
            # Show spinner while waiting for response
            start_time = time.time()
            
            try:
                with Live(Text(""), refresh_per_second=10) as live:
                    while not response_received and (time.time() - start_time) < args.timeout:
                        live.update(Text(f"[bold green]Chatbot is thinking {next(spinner_iter)}[/bold green]"))
                        time.sleep(0.1)
            except Exception as e:
                # Fallback if Live display fails
                while not response_received and (time.time() - start_time) < args.timeout:
                    print(f"\rChatbot is thinking...", end="")
                    time.sleep(0.5)
                print("\r                         ", end="\r")  # Clear the line
            
            # Check if we got a response or timed out
            if not response_received:
                console.print("\n[bold yellow]Response is taking too long. Request might have timed out.[/bold yellow]")
                response_received = True  # Stop the thread from updating the response
            
            # Display response
            console.print("[bold green]Chatbot[/bold green]")
            console.print(Markdown(response[0]))
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        
if __name__ == "__main__":
    main()
