#!/usr/bin/env python3
"""
Test simple del servidor FastAPI
"""

import sys
import os

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Simple Test")

@app.get("/")
async def root():
    return {"message": "Server is running"}

@app.get("/test")
async def test():
    return {"status": "ok", "message": "Simple test endpoint"}

if __name__ == "__main__":
    print("🚀 Iniciando servidor simple...")
    uvicorn.run("simple_test:app", host="0.0.0.0", port=8000, reload=True)