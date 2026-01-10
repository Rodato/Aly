import os
from pathlib import Path
from docling.document_converter import DocumentConverter
from rag_assistant import RAGAssistant

def convert_docs_to_markdown():
    """Convierte todos los PDFs y DOCX en documents/ a markdown."""
    documents_path = Path("./documents")
    markdown_path = Path("./markdown_docs")
    markdown_path.mkdir(exist_ok=True)
    
    # Inicializar el convertidor de docling
    converter = DocumentConverter()
    
    print("🔄 Convirtiendo documentos a Markdown...")
    
    converted_files = []
    
    for file_path in documents_path.glob("*"):
        if file_path.suffix.lower() in ['.pdf', '.docx', '.doc']:
            print(f"📄 Procesando: {file_path.name}")
            
            try:
                # Convertir documento con docling
                result = converter.convert(file_path)
                
                # Obtener el contenido en markdown
                markdown_content = result.document.export_to_markdown()
                
                # Guardar como markdown
                output_file = markdown_path / f"{file_path.stem}.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                converted_files.append(output_file)
                print(f"✅ Convertido: {output_file.name}")
                
            except Exception as e:
                print(f"❌ Error procesando {file_path.name}: {str(e)}")
                continue
    
    print(f"\n🎉 Conversión completada: {len(converted_files)} archivos procesados")
    return converted_files

def create_embeddings():
    """Crea los embeddings de todos los documentos markdown."""
    print("\n🔄 Creando embeddings...")
    
    # Inicializar RAG Assistant
    assistant = RAGAssistant()
    
    try:
        # Crear base de datos vectorial desde archivos markdown
        assistant.create_vectorstore_from_markdown("./markdown_docs")
        print("✅ Base de datos vectorial creada exitosamente")
        
    except Exception as e:
        print(f"❌ Error creando embeddings: {str(e)}")
        return False
    
    return True

def main():
    """Proceso completo de preprocesamiento."""
    print("🚀 Iniciando preprocesamiento de documentos...")
    
    # Paso 1: Convertir documentos a markdown
    converted_files = convert_docs_to_markdown()
    
    if not converted_files:
        print("❌ No se pudieron convertir documentos")
        return
    
    # Paso 2: Crear embeddings
    success = create_embeddings()
    
    if success:
        print("\n✨ ¡Preprocesamiento completado exitosamente!")
        print("\n📋 Próximos pasos:")
        print("1. Ejecuta: source venv/bin/activate")
        print("2. Ejecuta: streamlit run main.py")
        print("3. ¡Chatea con tus documentos!")
    else:
        print("\n❌ Error en el preprocesamiento")

if __name__ == "__main__":
    main()