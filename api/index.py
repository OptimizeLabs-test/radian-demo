"""
Vercel serverless function handler for FastAPI backend.
This file routes all /api/* requests to the FastAPI application.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Import the FastAPI app
from app.main import app

# Import Mangum to convert ASGI (FastAPI) to AWS Lambda/Vercel format
from mangum import Mangum

# Create the handler instance
# Note: lifespan="off" because serverless functions don't support startup/shutdown events
# The middleware in app.main will handle lazy initialization
handler = Mangum(app, lifespan="off")

