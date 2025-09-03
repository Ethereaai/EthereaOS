from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
import os

# Load config
from config import (
    LLM_API_BASE,
    LLM_COMPLETION_ENDPOINT,
    ETHREA_PROMPT_FILE,
    DEFAULT_N_PREDICT,
    DEFAULT_TEMP,
    DEFAULT_TOP_P,
)

app = FastAPI(title="Etherea OS - Core AI")

# Allow frontend to connect (your Etherea OS UI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your domain
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fix: Point to the parent directory where your HTML files actually are
current_dir = os.path.dirname(os.path.abspath(__file__))  # etherea-api/
parent_dir = os.path.dirname(current_dir)  # ETHEREA_OS/

# Mount static files from the parent directory
app.mount("/assets", StaticFiles(directory=os.path.join(parent_dir, "assets")), name="assets")

# Serve index.html at root - now pointing to correct location
@app.get("/")
async def read_root():
    index_path = os.path.join(parent_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Index file not found")

# Also serve common static files - now pointing to correct location
@app.get("/manifest.json")
async def manifest():
    manifest_path = os.path.join(parent_dir, "manifest.json")
    if os.path.exists(manifest_path):
        return FileResponse(manifest_path)
    raise HTTPException(status_code=404, detail="Manifest not found")

@app.get("/service-worker.js")
async def service_worker():
    sw_path = os.path.join(parent_dir, "service-worker.js")
    if os.path.exists(sw_path):
        return FileResponse(sw_path)
    raise HTTPException(status_code=404, detail="Service worker not found")

@app.get("/settings.html")
async def settings():
    settings_path = os.path.join(parent_dir, "settings.html")
    if os.path.exists(settings_path):
        return FileResponse(settings_path)
    raise HTTPException(status_code=404, detail="Settings page not found")

# Load Etherea's personality at startup
@app.on_event("startup")
async def load_system_prompt():
    global SYSTEM_PROMPT
    if not os.path.exists(ETHREA_PROMPT_FILE):
        raise RuntimeError(f"System prompt file not found: {ETHREA_PROMPT_FILE}")
    with open(ETHREA_PROMPT_FILE, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()

# Hold system prompt in memory
SYSTEM_PROMPT = None

# Chat Request Model
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    n_predict: int = DEFAULT_N_PREDICT
    temp: float = DEFAULT_TEMP
    top_p: float = DEFAULT_TOP_P

# Chat Endpoint
@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not SYSTEM_PROMPT:
        raise HTTPException(status_code=500, detail="Etherea's mind is not loaded yet.")

    # Build full prompt using Llama 3 template
    full_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{SYSTEM_PROMPT}<|eot_id|><|start_header_id|>user<|end_header_id|>\n{request.message.strip()}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"

    # Send to llama-server
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                LLM_API_BASE + LLM_COMPLETION_ENDPOINT,
                json={
                    "prompt": full_prompt,
                    "n_predict": request.n_predict,
                    "temperature": request.temp,
                    "top_p": request.top_p,
                    "stop": ["<|eot_id|>"],
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            reply = data.get("content", "").strip()

            # Check if it's a tool command
            if reply.startswith("TOOL_COMMAND:"):
                return {"role": "tool", "command": reply, "text": None}

            return {"role": "chat", "text": reply, "command": None}

        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Cannot connect to LLM server. Is llama-server running?")
        except httpx.ReadTimeout:
            raise HTTPException(status_code=504, detail="LLM server timed out")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

# Health Check
@app.get("/api/health")
def health():
    return {"status": "online", "agent": "Etherea", "model": "Phi-3-Mini-3.8B-Instruct"}

# Debug endpoint to check file paths (remove this in production)
@app.get("/debug/paths")
def debug_paths():
    current = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(current)
    return {
        "current_dir": current,
        "parent_dir": parent,
        "index_exists": os.path.exists(os.path.join(parent, "index.html")),
        "assets_exists": os.path.exists(os.path.join(parent, "assets")),
        "files_in_parent": os.listdir(parent) if os.path.exists(parent) else "parent not found"
    }