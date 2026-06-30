from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil
from pdf_compressor import compress_pdf

app = FastAPI(title="PDF Compressor API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import tempfile

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pdf_compressor_temp")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Ensure directories exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

import threading

# Thread-safe task status store
tasks_status = {}  # {task_id: {"status": "processing", "progress": 0, "message": "Iniciando...", "stats": None, "error": None}}
tasks_status_lock = threading.Lock()

def update_task_status(task_id: str, status: str, progress: int, message: str, stats: dict = None, error: str = None):
    with tasks_status_lock:
        tasks_status[task_id] = {
            "status": status,
            "progress": progress,
            "message": message,
            "stats": stats,
            "error": error
        }

def clean_task_status(task_id: str):
    with tasks_status_lock:
        tasks_status.pop(task_id, None)

def remove_file(path: str):
    """Utility function to delete a file. Used as a background task after downloading."""
    try:
        if os.path.exists(path):
            os.remove(path)
            print(f"Cleaned up temporary file: {path}")
    except Exception as e:
        print(f"Error removing temporary file {path}: {e}")

def run_compression_task(
    task_id: str,
    original_filename: str,
    input_path: str,
    output_path: str,
    quality: int,
    scale: float,
    grayscale: bool,
    remove_metadata: bool
):
    def progress_callback(progress: int, message: str):
        update_task_status(task_id, "processing", progress, message)
        
    try:
        # Initial status
        update_task_status(task_id, "processing", 5, "Preparando arquivo...")
        
        # Run compression
        stats = compress_pdf(
            input_path=input_path,
            output_path=output_path,
            quality=quality,
            scale=scale,
            grayscale=grayscale,
            remove_metadata=remove_metadata,
            progress_callback=progress_callback
        )
        
        # Inject filename into stats
        stats["filename"] = original_filename
        
        # Mark as completed
        update_task_status(task_id, "completed", 100, "Compactação concluída!", stats=stats)
        
    except Exception as e:
        print(f"Error in compression task {task_id}: {e}")
        update_task_status(task_id, "failed", 100, f"Erro: {str(e)}", error=str(e))
        # Delete output file if partially created
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
    finally:
        # Always clean up the input file
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass

@app.post("/api/compress")
async def api_compress_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    quality: int = Form(70),
    scale: float = Form(0.7),
    grayscale: bool = Form(False),
    remove_metadata: bool = Form(True)
):
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    task_id = str(uuid.uuid4())
    input_path = os.path.join(TEMP_DIR, f"{task_id}_input.pdf")
    output_path = os.path.join(TEMP_DIR, f"{task_id}.pdf")
    
    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Initialize status
        update_task_status(task_id, "processing", 0, "Iniciando upload...")
        
        # Start compression as a background task
        background_tasks.add_task(
            run_compression_task,
            task_id,
            file.filename,
            input_path,
            output_path,
            quality,
            scale,
            grayscale,
            remove_metadata
        )
        
        return JSONResponse(content={
            "success": True,
            "task_id": task_id,
            "status_url": f"/api/status/{task_id}"
        })
        
    except Exception as e:
        # Clean up input file if saving fails
        if os.path.exists(input_path):
            os.remove(input_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    with tasks_status_lock:
        status = tasks_status.get(task_id)
        
    if not status:
        raise HTTPException(status_code=404, detail="Task not found or expired.")
        
    response_data = {
        "status": status["status"],
        "progress": status["progress"],
        "message": status["message"]
    }
    
    if status["status"] == "completed":
        response_data["download_url"] = f"/api/download/{task_id}"
        response_data["stats"] = status["stats"]
    elif status["status"] == "failed":
        response_data["error"] = status["error"]
        
    return JSONResponse(content=response_data)

@app.get("/api/download/{task_id}")
async def download_file(task_id: str, background_tasks: BackgroundTasks):
    file_path = os.path.join(TEMP_DIR, f"{task_id}.pdf")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found or already downloaded.")
        
    # Queue the file deletion and status cleaning to run after the response is sent
    background_tasks.add_task(remove_file, file_path)
    background_tasks.add_task(clean_task_status, task_id)
    
    return FileResponse(
        file_path, 
        media_type="application/pdf", 
        filename="compressed.pdf"
    )

# Mount static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(content={"message": "PDF Compressor API is running. Static files are missing."})

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting PDF Compressor local server on http://{host}:{port}")
    # Disable reload in production to prevent server restart triggers on file writes
    uvicorn.run("main:app", host=host, port=port, reload=False)
