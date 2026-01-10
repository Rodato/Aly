#!/usr/bin/env python3
"""
Update Titles MongoDB - Actualiza títulos en la base de datos MongoDB
"""

import os
import sys
import logging
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

# Agregar scripts al path
sys.path.append('scripts')
from enhanced_chunker import TitleExtractor

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoTitleUpdater:
    """Actualizador de títulos en MongoDB."""
    
    def __init__(self):
        self.uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("MONGODB_DB_NAME")
        self.collection_name = os.getenv("MONGODB_COLLECTION_NAME")
        
        if not all([self.uri, self.db_name, self.collection_name]):
            raise ValueError("Variables MongoDB no configuradas")
        
        # Conectar a MongoDB
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]
        
        logger.info(f"📡 Conectado a MongoDB: {self.db_name}.{self.collection_name}")
        
        # Inicializar extractor de títulos
        self.title_extractor = TitleExtractor()
    
    def get_document_mapping(self):
        """Obtiene mapeo de documentos existentes."""
        # Mapeo de nombres de archivo a nuevos títulos
        title_mapping = {
            "MANUAL Borrador GBI Mexico": "Manual de Metodología GBI México",
            "Revisions Complete_BOYS CLUB CURRICULUM": "Guía para Implementar Clubes de Niños", 
            "Revisions Complete_CLASSROOM RESOURCE-Revised Aug 2025.docx": "Guía de Clase para Engajar Niños en la Educación",
            "Revisions Complete_EDUCATOR'S GUIDE-Revised Aug 2025": "Guía para Educadores: Engaging Boys in Education",
            "Revisions Complete_PARENTS GUIDE RESOURCE_Revised Aug 2025": "Guía para Padres y Cuidadores: Apoyo a la Educación de Niños",
            "3. MANUAL A+P_vICBF.docx": "Manual de Facilitación A+P"
        }
        
        return title_mapping
    
    def update_all_titles(self):
        """Actualiza títulos para todos los documentos."""
        title_mapping = self.get_document_mapping()
        
        print("🔄 Actualizando títulos en MongoDB...")
        print("="*60)
        
        updated_docs = []
        
        for document_name, new_title in title_mapping.items():
            print(f"\\n📄 Documento: {document_name}")
            print(f"🆕 Nuevo título: '{new_title}'")
            
            try:
                # Contar chunks antes
                chunk_count = self.collection.count_documents({"document_name": document_name})
                
                if chunk_count == 0:
                    print(f"⚠️  No se encontraron chunks para: {document_name}")
                    continue
                
                # Actualizar título en todos los chunks del documento
                result = self.collection.update_many(
                    {"document_name": document_name},
                    {"$set": {"document_title": new_title}}
                )
                
                if result.modified_count > 0:
                    print(f"✅ Actualizados {result.modified_count} chunks")
                    updated_docs.append({
                        "document": document_name,
                        "new_title": new_title,
                        "chunks_updated": result.modified_count
                    })
                else:
                    print(f"⚠️  No se actualizaron chunks (quizás ya tenían el título correcto)")
                    
            except Exception as e:
                print(f"❌ Error actualizando {document_name}: {e}")
        
        print("\\n" + "="*60)
        print("📊 RESUMEN DE ACTUALIZACIONES:")
        
        total_chunks = 0
        for doc in updated_docs:
            print(f"  📄 {doc['document']}")
            print(f"      ✅ {doc['chunks_updated']} chunks actualizados")
            print(f"      🆕 Título: {doc['new_title']}")
            total_chunks += doc['chunks_updated']
        
        print(f"\\n🎉 Total: {len(updated_docs)} documentos, {total_chunks} chunks actualizados")
    
    def verify_titles(self):
        """Verifica los títulos actualizados."""
        print("\\n🔍 Verificando títulos actualizados...")
        
        # Obtener documentos únicos con sus títulos
        pipeline = [
            {
                "$group": {
                    "_id": "$document_name",
                    "document_title": {"$first": "$document_title"},
                    "chunk_count": {"$sum": 1}
                }
            },
            {"$sort": {"chunk_count": -1}}
        ]
        
        results = list(self.collection.aggregate(pipeline))
        
        print("\\n📋 Títulos actuales en MongoDB:")
        for doc in results:
            print(f"  📄 {doc['_id']} ({doc['chunk_count']} chunks)")
            print(f"      📝 Título: {doc['document_title']}")
        
        return results
    
    def close(self):
        """Cierra conexión."""
        if hasattr(self, 'client'):
            self.client.close()


def main():
    """Función principal."""
    try:
        updater = MongoTitleUpdater()
        
        # Mostrar títulos actuales
        print("📊 Estado actual:")
        current_titles = updater.verify_titles()
        
        # Confirmar actualización
        print("\\n" + "="*60)
        response = input("¿Proceder con la actualización de títulos? (s/n): ").strip().lower()
        
        if response in ['s', 'si', 'yes', 'y']:
            # Actualizar títulos
            updater.update_all_titles()
            
            # Verificar resultados
            print("\\n🔍 Verificación post-actualización:")
            updater.verify_titles()
            
            print("\\n✅ ¡Actualización completada!")
        else:
            print("❌ Actualización cancelada")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        if 'updater' in locals():
            updater.close()


if __name__ == "__main__":
    main()