"""
Backend main entry point
Imports the FastAPI app from the api module
"""

from backend.api.main import app

# This allows uvicorn backend.main:app to work
__all__ = ["app"] 