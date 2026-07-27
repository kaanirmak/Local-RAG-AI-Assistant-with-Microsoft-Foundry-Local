# FastAPI server — serves UI, handles chat via SSE, manages model lifecycle
import os
import logging
import json
import threading
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from src.config import CONFIG
from src.vector_store import VectorStore
from src.chat_engine import ChatEngine
from src.chunker import process_document

# --- SDK Patching ---
# The foundry_local package version <= 0.5.1 has a bug where post_with_progress blocks
# indefinitely on iter_lines() even after the final JSON response containing success/failure
# is received, due to connection keep-alive. We patch it to break when JSON is complete.
import re
from tqdm import tqdm
from foundry_local.client import HttpxClient

def patched_post_with_progress(self, path: str, body=None):
    logging.getLogger("server").info("PATCH: patched_post_with_progress CALLED!")
    with self._client.stream("POST", path, json=body, timeout=None) as response:
        progress_bar = None
        prev_percent = 0.0
        # Access logger from the client module
        client_logger = logging.getLogger("foundry_local.client")
        if client_logger.isEnabledFor(logging.INFO):
            progress_bar = tqdm(total=100.0)
        final_json = ""
        for line in response.iter_lines():
            # Replace comma with dot to handle Turkish/European locales using comma as decimal separator
            normalized_line = line.replace(",", ".")
            if final_json or line.startswith("{"):
                final_json += line
                try:
                    # If valid JSON, the response is complete, we can exit the stream loop safely
                    result = json.loads(final_json)
                    if progress_bar:
                        progress_bar.update(100.0 - prev_percent)
                    break
                except ValueError:
                    pass
                continue
            if not progress_bar:
                # Still parse percent even if progress_bar logging is disabled, so status_manager is updated
                if match := re.search(r"(\d+(?:\.\d+)?)%", normalized_line):
                    percent = min(float(match.group(1)), 100.0)
                    status_manager.update("downloading", int(percent))
                continue
            if match := re.search(r"(\d+(?:\.\d+)?)%", normalized_line):
                percent = min(float(match.group(1)), 100.0)
                delta = percent - prev_percent
                if delta > 0:
                    progress_bar.update(delta)
                    prev_percent = percent
                status_manager.update("downloading", int(percent))
        if progress_bar:
            progress_bar.close()

        if not final_json.endswith("}"):
            raise ValueError(f"Invalid JSON response: {final_json}")

        return json.loads(final_json)

HttpxClient.post_with_progress = patched_post_with_progress

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("server")

app = FastAPI(title="Local RAG AI Assistant")

# --- State ---
class StatusManager:
    def __init__(self):
        self.status = "initializing"
        self.progress = 0
        self.error = None

    def update(self, status, progress=0, error=None):
        self.status = status
        self.progress = progress
        self.error = error

status_manager = StatusManager()
chat_engine = None

# --- Vector Store ---
vector_store = VectorStore(CONFIG["db_file"])

# --- Model Initialization Thread ---
def initialize_model():
    global chat_engine
    try:
        status_manager.update("initializing", 0)
        logger.info("Initializing Foundry Local...")

        from foundry_local import FoundryLocalManager
        import openai

        # Initialize manager which automatically starts service
        manager = FoundryLocalManager(bootstrap=True)
        logger.info("Service started successfully.")

        # Check if cached
        cached_models = manager.list_cached_models()
        is_cached = any(m.alias == CONFIG["model"] or m.id == CONFIG["model"] for m in cached_models)

        if not is_cached:
            status_manager.update("downloading", 0)
            logger.info("Downloading model...")
            # Blocking download call (will log automatically)
            manager.download_model(CONFIG["model"])
            logger.info("Download complete!")

        status_manager.update("loading", 0)
        logger.info("Loading model into memory...")
        model_info = manager.load_model(CONFIG["model"])

        endpoint = getattr(manager, "_service_uri", None) or "http://127.0.0.1:8000"
        logger.info(f"Connecting client to endpoint: {endpoint}")

        # Connect via OpenAI client
        openai_client = openai.OpenAI(
            base_url=f"{endpoint}/v1" if not endpoint.endswith("/v1") else endpoint,
            api_key="local"
        )

        chat_engine = ChatEngine(vector_store, openai_client, model_info.id)
        status_manager.update("ready", 100)
        logger.info("Model ready! Assistant is online.")

    except Exception as e:
        logger.error(f"Failed to initialize model: {e}", exc_info=True)
        status_manager.update("error", 0, error=str(e))
        
        # Fallback to no-LLM mode
        chat_engine = ChatEngine(vector_store, None)
        logger.info("Running in fallback mode (retrieval only, no LLM answers).")

# --- API Routes ---

@app.get("/api/status")
async def status_endpoint():
    async def event_generator():
        last_status = None
        last_progress = None
        last_error = None
        while True:
            if (status_manager.status != last_status or 
                status_manager.progress != last_progress or 
                status_manager.error != last_error):
                
                last_status = status_manager.status
                last_progress = status_manager.progress
                last_error = status_manager.error
                
                data = json.dumps({
                    "status": last_status,
                    "progress": last_progress,
                    "error": last_error
                })
                yield f"data: {data}\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

class ChatPayload(BaseModel):
    query: str

@app.post("/api/chat")
def chat_endpoint(payload: ChatPayload):
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    if chat_engine is None:
        raise HTTPException(status_code=503, detail="Model is still loading. Please wait.")

    def event_generator():
        for event in chat_engine.chat(payload.query.strip()):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

class UploadPayload(BaseModel):
    filename: str
    content: str

@app.post("/api/upload")
def upload_document(payload: UploadPayload):
    if not payload.filename or not payload.content:
        raise HTTPException(status_code=400, detail="Filename and content are required")

    name, ext = os.path.splitext(payload.filename.lower())
    if ext not in (".md", ".txt", ".pdf"):
        raise HTTPException(status_code=400, detail="Only .md, .txt, and .pdf files are supported")

    # Save file to docs/
    docs_dir = CONFIG["docs_dir"]
    os.makedirs(docs_dir, exist_ok=True)
    file_path = os.path.join(docs_dir, payload.filename)

    if ext == ".pdf":
        # PDF content is sent as base64 from the frontend
        import base64
        try:
            pdf_bytes = base64.b64decode(payload.content)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid PDF content encoding")

        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        # Extract text from the saved PDF
        try:
            import fitz  # PyMuPDF
            text_parts = []
            with fitz.open(file_path) as doc:
                for page in doc:
                    page_text = page.get_text("text")
                    if page_text.strip():
                        text_parts.append(page_text)
            text_content = "\n\n".join(text_parts)
        except ImportError:
            raise HTTPException(status_code=500, detail="PyMuPDF not installed. Run: pip install PyMuPDF")

        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No extractable text found in PDF")

        # Process and index extracted text
        chunks = process_document(text_content, payload.filename)
    else:
        # Text-based files (md, txt)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(payload.content)

        # Process and index
        chunks = process_document(payload.content, payload.filename)

    vector_store.add_chunks(chunks)

    logger.info(f"📄 Uploaded and indexed: {payload.filename} ({len(chunks)} chunks)")

    return {
        "success": True,
        "filename": payload.filename,
        "chunks": len(chunks)
    }


@app.get("/api/documents")
def get_documents():
    try:
        docs = vector_store.get_document_ids()
        count = vector_store.count()
        return {"documents": docs, "totalChunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {e}")

@app.post("/api/clear")
def clear_history():
    if chat_engine is not None:
        chat_engine.clear_history()
    return {"success": True}

# Startup logic
@app.on_event("startup")
def startup_event():
    # Start model loading in a background thread to prevent blocking FastAPI
    threading.Thread(target=initialize_model, daemon=True).start()

# Mount public directory at the end for static files (including index.html)
if os.path.exists("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
    logger.info("\n╔══════════════════════════════════════════════════╗")
    logger.info("║   🤖 Local RAG AI Assistant (Python)            ║")
    logger.info("║   Powered by Microsoft Foundry Local             ║")
    logger.info("╚══════════════════════════════════════════════════╝\n")
    uvicorn.run("src.server:app", host=CONFIG["host"], port=CONFIG["port"], log_level="info")
