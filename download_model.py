import os
import argparse
import requests
import platform
import subprocess
import sys
from tqdm import tqdm
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def download_file(url, destination):
    """Download a file with progress bar."""
    if os.path.exists(destination):
        console.print(f"[yellow]File already exists at {destination}[/yellow]")
        overwrite = input("Overwrite? (y/n): ").lower().strip() == 'y'
        if not overwrite:
            return False
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Get file size from response headers
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 KB
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Use tqdm safely
        with open(destination, 'wb') as file:
            with tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True, desc="Downloading") as progress_bar:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)
        
        return True
    except Exception as e:
        console.print(f"[bold red]Error during download: {str(e)}[/bold red]")
        # Clean up partial file
        if os.path.exists(destination):
            try:
                os.remove(destination)
                console.print("[yellow]Removed partial download file[/yellow]")
            except:
                pass
        return False

def check_system_specs():
    """Check system specifications to recommend appropriate model."""
    system_info = {}
    
    # Check OS
    system_info['os'] = platform.system()
    
    # Check RAM
    if system_info['os'] == 'Windows':
        try:
            import psutil
            ram_gb = round(psutil.virtual_memory().total / (1024**3))
            system_info['ram'] = f"{ram_gb} GB"
        except:
            system_info['ram'] = "Unknown"
    elif system_info['os'] == 'Linux':
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        ram_kb = int(line.split()[1])
                        ram_gb = round(ram_kb / (1024**2))
                        system_info['ram'] = f"{ram_gb} GB"
                        break
        except:
            system_info['ram'] = "Unknown"
    elif system_info['os'] == 'Darwin':  # macOS
        try:
            output = subprocess.check_output(['sysctl', '-n', 'hw.memsize']).strip()
            ram_bytes = int(output)
            ram_gb = round(ram_bytes / (1024**3))
            system_info['ram'] = f"{ram_gb} GB"
        except:
            system_info['ram'] = "Unknown"
    else:
        system_info['ram'] = "Unknown"
    
    # CPU info
    system_info['cpu'] = platform.processor() or "Unknown"
    system_info['cpu_count'] = os.cpu_count() or "Unknown"
    
    # GPU check - very basic
    system_info['has_gpu'] = False
    if system_info['os'] == 'Windows':
        try:
            output = subprocess.check_output(['wmic', 'path', 'win32_VideoController', 'get', 'name'], text=True)
            if 'NVIDIA' in output or 'AMD' in output:
                system_info['has_gpu'] = True
        except:
            pass
    
    return system_info

def main():
    # Check system specs
    system_specs = check_system_specs()
    
    # Display system info
    console.print(Panel.fit(
        f"[bold blue]System Information[/bold blue]\n"
        f"[cyan]OS:[/cyan] {system_specs['os']}\n"
        f"[cyan]RAM:[/cyan] {system_specs['ram']}\n"
        f"[cyan]CPU:[/cyan] {system_specs['cpu_count']} cores\n"
        f"[cyan]Dedicated GPU:[/cyan] {'Yes' if system_specs['has_gpu'] else 'No'}"
    ))
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Download GGUF model for the RAG chatbot")
    parser.add_argument("--model", choices=["tiny", "small", "medium", "large"], 
                        help="Model size to download")
    args = parser.parse_args()
    
    # Auto-recommend model based on system specs if not specified
    recommended = None
    ram_gb = 0
    
    if system_specs['ram'] != "Unknown":
        try:
            ram_gb = int(system_specs['ram'].split()[0])
        except:
            ram_gb = 0
    
    if ram_gb < 4:
        recommended = "tiny"
    elif ram_gb < 8:
        recommended = "small"
    elif ram_gb < 16:
        recommended = "medium"
    else:
        recommended = "large"
    
    # Use user choice or recommendation
    model_size = args.model or recommended
    
    # Show model options
    table = Table(title="Available Models")
    table.add_column("Size", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("RAM Required", style="yellow")
    table.add_column("Recommended For", style="blue")
    
    table.add_row("tiny", "TinyLlama 1.1B", "~2 GB", "Basic queries, low-spec machines")
    table.add_row("small", "Llama-2 7B", "~4-6 GB", "General purpose, balanced machines")
    table.add_row("medium", "Mistral 7B", "~4-6 GB", "Better quality, modern machines")
    table.add_row("large", "Llama-2 13B", "~8-10 GB", "Best quality, powerful machines")
    
    console.print(table)
    console.print(f"[bold green]Recommended model for your system:[/bold green] [yellow]{recommended}[/yellow]")
    
    if not args.model:
        choices = ["tiny", "small", "medium", "large"]
        choice_idx = choices.index(recommended)
        
        console.print("\nSelect a model to download:")
        for i, size in enumerate(choices):
            marker = ">" if i == choice_idx else " "
            console.print(f" {marker} [{i+1}] {size}")
        
        selection = input("\nEnter your choice (or press Enter for recommended): ").strip()
        
        if selection and selection.isdigit() and 1 <= int(selection) <= 4:
            model_size = choices[int(selection) - 1]
        else:
            model_size = recommended
    
    models = {
        "tiny": {
            "name": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            "size": "~600 MB",
            "description": "Very fast, suitable for older computers"
        },
        "small": {
            "name": "llama-2-7b-chat.Q4_K_M.gguf",
            "url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf",
            "size": "~4 GB",
            "description": "Good balance of quality and speed"
        },
        "medium": {
            "name": "mistral-7b-instruct-v0.1.Q4_K_M.gguf", 
            "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf",
            "size": "~4 GB",
            "description": "High quality responses"
        },
        "large": {
            "name": "llama-2-13b-chat.Q4_K_M.gguf",
            "url": "https://huggingface.co/TheBloke/Llama-2-13B-Chat-GGUF/resolve/main/llama-2-13b-chat.Q4_K_M.gguf", 
            "size": "~8 GB",
            "description": "Best quality, requires more RAM"
        }
    }
    
    selected = models[model_size]
    model_path = os.path.join("models", selected["name"])
    
    console.print(Panel.fit(
        f"[bold blue]Downloading {selected['name']}[/bold blue]\n"
        f"[cyan]File size: {selected['size']}[/cyan]\n"
        f"[green]{selected['description']}[/green]"
    ))
    
    try:
        success = download_file(selected["url"], model_path)
        if success:
            # Update .env file if it exists
            env_file = ".env"
            if os.path.exists(env_file):
                with open(env_file, "r") as f:
                    lines = f.readlines()
                
                updated = False
                with open(env_file, "w") as f:
                    for line in lines:
                        if line.startswith("MODEL_PATH="):
                            f.write(f"MODEL_PATH={model_path}\n")
                            updated = True
                        else:
                            f.write(line)
                    
                    if not updated:
                        f.write(f"\nMODEL_PATH={model_path}\n")
            else:
                with open(env_file, "w") as f:
                    f.write(f"MODEL_PATH={model_path}\n")
            
            console.print(f"[bold green]Download complete! Model saved to {model_path}[/bold green]")
            console.print("[green]Model path has been updated in your .env file.[/green]")
            console.print("[cyan]Run the chatbot with: python main.py[/cyan]")
        
    except Exception as e:
        console.print(f"[bold red]Error downloading model: {e}[/bold red]")
        console.print("[yellow]You can manually download a GGUF model from https://huggingface.co/models?sort=downloads&search=gguf[/yellow]")

if __name__ == "__main__":
    main()
