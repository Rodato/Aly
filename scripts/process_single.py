#!/usr/bin/env python3
"""
Procesa un solo documento específico
"""

import os
from pathlib import Path
from docling.document_converter import DocumentConverter

def process_single_document(filename):
    """Procesa un documento específico."""
    input_folder = Path("documents")
    output_folder = Path("DocsMD")
    
    # Crear carpeta de salida
    output_folder.mkdir(exist_ok=True)
    
    # Encontrar archivo
    file_path = input_folder / filename
    
    if not file_path.exists():
        print(f"❌ Archivo no encontrado: {filename}")
        return False
    
    print(f"🚀 Procesando: {filename}")
    
    # Inicializar conversor
    converter = DocumentConverter()
    
    try:
        # Convertir
        print("  🔄 Convirtiendo con Docling...")
        result = converter.convert(file_path)
        markdown_content = result.document.export_to_markdown()
        
        # Guardar
        md_path = output_folder / f"{file_path.stem}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"  ✅ Completado: {md_path.name}")
        print(f"  📏 Tamaño: {len(markdown_content):,} caracteres")
        print(f"  📄 Archivo: {md_path}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

def main():
    # Procesar el documento faltante
    filename = "3. MANUAL A+P_vICBF.docx.pdf"
    success = process_single_document(filename)
    
    if success:
        print(f"\n✨ ¡Documento procesado exitosamente!")
    else:
        print(f"\n❌ Error procesando el documento")

if __name__ == "__main__":
    main()