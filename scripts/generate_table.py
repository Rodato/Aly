#!/usr/bin/env python3
"""
Genera tabla de estado de procesamiento de documentos
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime

def main():
    print("📋 GENERANDO TABLA DE ESTADO DE DOCUMENTOS")
    print("="*60)
    
    input_folder = Path("documents")
    output_folder = Path("DocsMD")
    
    # Obtener archivos de entrada
    supported_extensions = {'.pdf', '.docx', '.doc', '.pptx'}
    input_files = [f for f in input_folder.iterdir() 
                   if f.is_file() and f.suffix.lower() in supported_extensions]
    
    # Obtener archivos MD generados
    md_files = list(output_folder.glob('*.md'))
    
    # Crear tabla de datos
    table_data = []
    
    for file_path in sorted(input_files):
        # Buscar archivo MD correspondiente
        expected_md = output_folder / f"{file_path.stem}.md"
        md_exists = expected_md.exists()
        
        # Información del archivo original
        original_size_kb = file_path.stat().st_size / 1024
        
        # Información del archivo MD si existe
        md_size_kb = 0
        md_chars = 0
        if md_exists:
            md_size_kb = expected_md.stat().st_size / 1024
            try:
                with open(expected_md, 'r', encoding='utf-8') as f:
                    md_chars = len(f.read())
            except:
                pass
        
        row = {
            "📄 Documento Original": file_path.name,
            "📏 Tamaño Original (KB)": f"{original_size_kb:.1f}",
            "📄 Archivo Markdown": expected_md.name if md_exists else "N/A",
            "✅ MD Generado": "✅ Sí" if md_exists else "❌ No",
            "📏 Tamaño MD (KB)": f"{md_size_kb:.1f}" if md_exists else "0.0",
            "📝 Caracteres MD": f"{md_chars:,}" if md_chars > 0 else "0",
            "📅 Estado": "✅ Completado" if md_exists else "⏳ Pendiente"
        }
        
        table_data.append(row)
    
    # Mostrar tabla
    if table_data:
        df = pd.DataFrame(table_data)
        print(df.to_string(index=False))
        
        # Guardar como CSV
        report_path = "tabla_documentos.csv"
        df.to_csv(report_path, index=False, encoding='utf-8')
        
        # Estadísticas
        total_docs = len(input_files)
        processed_docs = len([f for f in input_files 
                             if (output_folder / f"{f.stem}.md").exists()])
        
        print(f"\n📊 ESTADÍSTICAS:")
        print("-" * 40)
        print(f"📄 Total documentos: {total_docs}")
        print(f"✅ Procesados: {processed_docs}")
        print(f"⏳ Pendientes: {total_docs - processed_docs}")
        print(f"📈 Completado: {(processed_docs/total_docs)*100:.1f}%")
        print(f"📁 Archivos MD: {len(md_files)}")
        
        total_original_mb = sum(f.stat().st_size for f in input_files) / (1024*1024)
        total_md_mb = sum(f.stat().st_size for f in md_files) / (1024*1024)
        
        print(f"\n💾 TAMAÑOS:")
        print("-" * 40)
        print(f"📄 Total original: {total_original_mb:.1f} MB")
        print(f"📝 Total Markdown: {total_md_mb:.1f} MB")
        print(f"📉 Reducción: {((total_original_mb - total_md_mb)/total_original_mb)*100:.1f}%")
        
        print(f"\n💾 Tabla guardada en: {report_path}")
        
    else:
        print("❌ No se encontraron documentos para procesar")
    
    print(f"\n📁 ARCHIVOS MARKDOWN GENERADOS:")
    print("-" * 50)
    if md_files:
        for md_file in sorted(md_files):
            size_kb = md_file.stat().st_size / 1024
            print(f"  📄 {md_file.name} ({size_kb:.1f} KB)")
    else:
        print("  (Ningún archivo Markdown generado)")

if __name__ == "__main__":
    main()