import os
from pathlib import Path
import requests
from dotenv import load_dotenv
import PyPDF2
import chromadb
from typing import List, Dict

load_dotenv()

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrae texto de un PDF usando PyPDF2."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extrayendo texto de {pdf_path.name}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Divide el texto en chunks."""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        
        if end >= len(text):
            break
    
    return chunks

def get_embedding(text: str, api_key: str) -> List[float]:
    """Obtiene embedding de OpenRouter."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "openai/text-embedding-ada-002",
        "input": text[:8000]  # Límite de tokens
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result["data"][0]["embedding"]
    except Exception as e:
        print(f"Error obteniendo embedding: {e}")
        return [0.0] * 1536  # Embedding vacío como fallback

def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY no encontrada")
        return
    
    documents_path = Path("./documents")
    print("🚀 Procesando documentos...")
    
    all_chunks = []
    all_metadata = []
    
    # Procesar cada archivo PDF
    for pdf_file in documents_path.glob("*.pdf"):
        print(f"📄 Procesando: {pdf_file.name}")
        
        # Extraer texto
        text = extract_text_from_pdf(pdf_file)
        if not text.strip():
            print(f"⚠️ No se pudo extraer texto de {pdf_file.name}")
            continue
        
        # Crear chunks
        chunks = chunk_text(text)
        print(f"  ➤ {len(chunks)} chunks creados")
        
        # Agregar a listas
        all_chunks.extend(chunks)
        all_metadata.extend([{
            "source": pdf_file.name,
            "chunk": i,
            "total_chunks": len(chunks)
        } for i in range(len(chunks))])
    
    if not all_chunks:
        print("❌ No se encontraron chunks para procesar")
        return
    
    print(f"\n📊 Total: {len(all_chunks)} chunks de {len(set(m['source'] for m in all_metadata))} documentos")
    print("🔄 Creando embeddings...")
    
    # Crear ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # Eliminar colección existente si existe
    try:
        chroma_client.delete_collection("documents")
    except:
        pass
    
    collection = chroma_client.create_collection("documents")
    
    # Procesar en lotes para evitar timeouts
    batch_size = 10
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i:i+batch_size]
        batch_metadata = all_metadata[i:i+batch_size]
        
        print(f"📦 Procesando lote {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")
        
        # Obtener embeddings para el lote
        embeddings = []
        for chunk in batch_chunks:
            embedding = get_embedding(chunk, api_key)
            embeddings.append(embedding)
        
        # Agregar a ChromaDB
        collection.add(
            embeddings=embeddings,
            documents=batch_chunks,
            metadatas=batch_metadata,
            ids=[f"doc_{i+j}" for j in range(len(batch_chunks))]
        )
    
    print("✅ ¡Base de datos creada exitosamente!")
    print(f"📍 Ubicación: ./chroma_db")
    print(f"📚 Total documentos: {collection.count()}")
    
    # Prueba rápida
    print("\n🧪 Prueba rápida...")
    query_embedding = get_embedding("¿De qué tratan los documentos?", api_key)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2
    )
    
    if results["documents"][0]:
        print("✅ Consulta de prueba exitosa")
        print(f"📄 Fuente: {results['metadatas'][0][0]['source']}")
    
    print("\n🎉 ¡Listo! Ahora puedes ejecutar la app con:")
    print("source venv/bin/activate && streamlit run main.py")

if __name__ == "__main__":
    main()