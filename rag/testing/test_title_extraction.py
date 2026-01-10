#!/usr/bin/env python3
"""
Test Title Extraction - Prueba el nuevo extractor de títulos
"""

import sys
sys.path.append('scripts')

from pathlib import Path
from enhanced_chunker import TitleExtractor

def test_title_extraction():
    """Prueba la extracción de títulos con LLM."""
    
    extractor = TitleExtractor()
    
    # Documentos a probar
    test_files = [
        "MANUAL Borrador GBI Mexico .md",
        "Revisions Complete_BOYS CLUB CURRICULUM.md", 
        "Revisions Complete_CLASSROOM RESOURCE-Revised Aug 2025.docx.md",
        "Revisions Complete_EDUCATOR'S GUIDE-Revised Aug 2025.md",
        "Revisions Complete_PARENTS GUIDE RESOURCE_Revised Aug 2025.md",
        "3. MANUAL A+P_vICBF.docx.md"
    ]
    
    print("🧪 PRUEBA DE EXTRACCIÓN DE TÍTULOS CON LLM")
    print("="*60)
    
    for filename in test_files:
        file_path = Path(f"data/processed/DocsMD/{filename}")
        
        if file_path.exists():
            print(f"\n📄 Archivo: {filename}")
            
            # Leer contenido
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraer título
            if extractor.use_llm:
                print("🤖 Usando LLM...")
                title = extractor.extract_title(content, filename)
            else:
                print("📝 Usando fallback...")
                title = extractor.extract_title_fallback(filename)
            
            print(f"✅ Título extraído: '{title}'")
            
        else:
            print(f"❌ Archivo no encontrado: {filename}")
    
    print(f"\n📊 Modo LLM: {'Activado' if extractor.use_llm else 'Desactivado (fallback)'}")

if __name__ == "__main__":
    test_title_extraction()