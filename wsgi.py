import os
import asyncio
from app import run_server


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("Servers shut down by keyboard interrupt")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
