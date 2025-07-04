"""
Main entry point for the orchestrator service.
"""

import argparse
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.orchestrator.app import run_server


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="FastAPI Orchestrating Service"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=os.getenv("RELOAD", "false").lower() == "true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "info"),
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level (default: info)"
    )
    parser.add_argument(
        "--config",
        default=os.getenv("CONFIG_PATH", "config/config.yaml"),
        help="Configuration file path (default: config/config.yaml)"
    )
    
    args = parser.parse_args()
    
    # Set config path environment variable
    os.environ["CONFIG_PATH"] = args.config
    
    print(f"Starting Orchestrator API server...")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Config: {args.config}")
    print(f"Log Level: {args.log_level}")
    print(f"Reload: {args.reload}")
    print()
    
    try:
        run_server(
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()