from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
import shutil
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno
load_dotenv()

# Configuración básica
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PlatformAPI")

# Inicializar Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("⚠️ SUPABASE_URL o SUPABASE_KEY no configuradas. El backend funcionará limitado.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

app = FastAPI(
    title="Puddle Bot Platform API",
    description="API para gestionar y ejecutar múltiples agentes inteligentes",
    version="0.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorio temporal para uploads
UPLOAD_DIR = Path("tmp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Modelos Pydantic (DTOs)
class BotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7

class BotResponse(BotCreate):
    id: str
    is_active: bool

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

# --- Funciones Auxiliares ---

def process_document_background(bot_id: str, file_path: Path):
    """
    Función en segundo plano que procesará el documento.
    Aquí conectaremos con tu script 'complete_pipeline.py' real.
    """
    logger.info(f"🔄 Procesando documento {file_path.name} para bot {bot_id}...")
    
    # TODO: Invocar lógica real de Docling + Embeddings
    # Por ahora simulamos un delay
    import time
    time.sleep(5)
    
    logger.info(f"✅ Documento {file_path.name} procesado y listo para RAG.")
    
    # Limpiar archivo temporal
    # os.remove(file_path)

# --- Rutas de Gestión de Bots ---

@app.get("/")
def health_check():
    return {"status": "active", "system": "Puddle Platform", "db_connected": supabase is not None}

@app.post("/bots", response_model=BotResponse)
def create_bot(bot: BotCreate):
    """Crea un nuevo bot en la plataforma."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        data = bot.dict()
        response = supabase.table("bots").insert(data).execute()
        if not response.data:
             raise HTTPException(status_code=500, detail="Failed to create bot")
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bots", response_model=List[BotResponse])
def list_bots():
    """Lista todos los bots disponibles."""
    if not supabase:
        return []
        
    try:
        response = supabase.table("bots").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error listing bots: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bots/{bot_id}", response_model=BotResponse)
def get_bot(bot_id: str):
    """Obtiene la configuración de un bot específico."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
        
    try:
        response = supabase.table("bots").select("*").eq("id", bot_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Bot not found")
        return response.data[0]
    except Exception as e:
        logger.error(f"Error getting bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bots/{bot_id}/documents")
async def upload_document(bot_id: str, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Sube un documento PDF/DOCX para indexarlo en el conocimiento del bot."""
    
    file_location = UPLOAD_DIR / f"{bot_id}_{file.filename}"
    
    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
            
        logger.info(f"📂 Archivo recibido: {file.filename} para bot {bot_id}")
        
        # Lanzar procesamiento en background (no bloquea la respuesta HTTP)
        background_tasks.add_task(process_document_background, bot_id, file_location)
        
        return {
            "filename": file.filename, 
            "status": "processing", 
            "message": "Archivo subido exitosamente. El procesamiento ha comenzado."
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")


# --- Rutas de Ejecución (Chat) ---

@app.post("/bots/{bot_id}/chat")
async def chat_with_bot(bot_id: str, request: ChatRequest):
    """
    Endpoint principal para chatear con un bot específico.
    Aquí es donde ocurrirá la magia de instanciar el LangGraph dinámicamente.
    """
    logger.info(f"Chat request for bot {bot_id}: {request.message}")
    
    # 1. Cargar configuración del bot (DB)
    # 2. Instanciar grafo (Agent Factory)
    # 3. Ejecutar run
    
    return {
        "bot_id": bot_id,
        "response": f"Esta es una respuesta simulada del bot {bot_id}. Aún no estoy conectado al cerebro real.",
        "usage": {"tokens": 15}
    }
