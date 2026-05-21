#!/usr/bin/env python3
"""
Standalone executable server for the Web Application.
This script bundles all backend functionality into a single executable.
"""

import os
import sys
import subprocess
import tempfile
import shutil

def check_dependencies():
    """Check if required Python packages are installed."""
    required_packages = [
        'fastapi', 'uvicorn', 'python-jose', 'passlib', 
        'python-multipart', 'sqlalchemy', 'psycopg2-binary',
        'pydantic', 'pydantic-settings', 'aiofiles'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    return missing


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])


def main():
    """Main entry point."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(script_dir, 'backend')
    
    if not os.path.exists(backend_dir):
        print(f"Error: Backend directory not found at {backend_dir}")
        sys.exit(1)
    
    os.chdir(backend_dir)
    
    # Check and install dependencies if needed
    missing = check_dependencies()
    if missing:
        print(f"Missing packages: {missing}")
        install_dependencies()
    
    # Set environment variables
    os.environ.setdefault('POSTGRES_USER', 'postgres')
    os.environ.setdefault('POSTGRES_PASSWORD', 'postgres')
    os.environ.setdefault('POSTGRES_DB', 'webapp')
    os.environ.setdefault('POSTGRES_HOST', 'localhost')
    os.environ.setdefault('POSTGRES_PORT', '5432')
    os.environ.setdefault('SECRET_KEY', 'your-super-secret-key-change-in-production')
    
    # Create uploads directory
    uploads_dir = os.path.join(backend_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    print("=" * 60)
    print("Web Application Server")
    print("=" * 60)
    print(f"Starting server on http://0.0.0.0:8000")
    print(f"API Documentation: http://0.0.0.0:8000/docs")
    print("=" * 60)
    print("\nNOTE: Make sure PostgreSQL is running and accessible.")
    print("Database connection: postgresql://postgres:postgres@localhost:5432/webapp\n")
    
    # Import and run the application
    from main import app
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
