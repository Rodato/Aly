import os
from pathlib import Path
from docling.document_converter import DocumentConverter
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import requests
from dotenv import load_dotenv
import json

load_dotenv()

class SimpleRAG:
    def __init__(self):
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.api_key = os.getenv("OPENROUTER_API_KEY")
    
    def convert_docs_to_text(self):
        """Convierte PDFs usando docling y extrae texto."""
        documents_path = Path("./documents")
        texts = []
        metadata = []
        
        converter = DocumentConverter()
        print("🔄 Convirtiendo documentos...")
        
        for file_path in documents_path.glob("*"):
            if file_path.suffix.lower() in ['.pdf', '.docx']:
                print(f"📄 Procesando: {file_path.name}")
                try:
                    result = converter.convert(file_path)
                    text_content = result.document.export_to_text()
                    
                    # Dividir en chunks
                    chunks = self.text_splitter.split_text(text_content)
                    
                    for i, chunk in enumerate(chunks):
                        texts.append(chunk)
                        metadata.append({
                            "source": file_path.name,
                            "chunk": i,
                            "total_chunks": len(chunks)
                        })
                    
                    print(f"✅ {file_path.name}: {len(chunks)} chunks")
                    
                except Exception as e:
                    print(f"❌ Error procesando {file_path.name}: {str(e)}")
                    continue
        
        print(f"\n🎉 Total: {len(texts)} chunks de {len(set(m['source'] for m in metadata))} documentos")
        return texts, metadata
    
    def get_embedding(self, text: str):
        """Obtiene embedding usando OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "openai/text-embedding-ada-002",
            "input": text
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result["data"][0]["embedding"]
        except Exception as e:
            print(f"Error obteniendo embedding: {str(e)}")
            return None
    
    def create_vectorstore(self):
        """Crea la base de datos vectorial."""
        texts, metadata = self.convert_docs_to_text()
        
        if not texts:
            print("❌ No hay textos para procesar")
            return
        
        print("\n🔄 Creando embeddings...")
        
        # Crear embeddings para cada texto
        embeddings_data = []
        for i, text in enumerate(texts):
            print(f"📊 Embedding {i+1}/{len(texts)}")
            embedding = self.get_embedding(text)
            if embedding:
                embeddings_data.append({
                    "text": text,
                    "embedding": embedding,
                    "metadata": metadata[i]
                })
        
        # Guardar en formato simple para Chroma
        import chromadb
        
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        collection = chroma_client.get_or_create_collection("documents")
        
        # Agregar documentos
        collection.add(
            embeddings=[d["embedding"] for d in embeddings_data],
            documents=[d["text"] for d in embeddings_data],
            metadatas=[d["metadata"] for d in embeddings_data],
            ids=[f"doc_{i}" for i in range(len(embeddings_data))]
        )
        
        print(f"✅ Base de datos creada con {len(embeddings_data)} documentos")
        return True
    
    def query(self, question: str, n_results: int = 3):
        """Realiza una consulta."""
        import chromadb
        
        # Obtener embedding de la pregunta
        question_embedding = self.get_embedding(question)
        if not question_embedding:
            return "Error obteniendo embedding de la pregunta"
        
        # Buscar documentos similares
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        collection = chroma_client.get_collection("documents")
        
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=n_results
        )
        
        if not results["documents"][0]:
            return "No se encontraron documentos relevantes"
        
        # Construir contexto
        context = "\n\n".join(results["documents"][0])
        
        # Generar respuesta
        response = self.generate_answer(context, question)
        
        return {
            "answer": response,
            "sources": results["metadatas"][0]
        }
    
    def generate_answer(self, context: str, question: str):
        """Genera respuesta usando el LLM."""
        prompt = f"""Basándote en el siguiente contexto, responde la pregunta de manera clara y concisa.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "mistralai/ministral-8b",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error generando respuesta: {str(e)}"

def main():
    print("🚀 Iniciando preprocesamiento...")
    
    rag = SimpleRAG()
    success = rag.create_vectorstore()
    
    if success:
        print("\n✨ ¡Preprocesamiento completado!")
        print("\nPrueba rápida:")
        result = rag.query("¿De qué tratan estos documentos?")
        print(f"Respuesta: {result['answer'][:200]}...")
    
if __name__ == "__main__":
    main()