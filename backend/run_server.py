#!/usr/bin/env python3
"""
Script to run the Green Agent FastAPI server.
"""
import uvicorn
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
