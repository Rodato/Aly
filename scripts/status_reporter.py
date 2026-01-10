#!/usr/bin/env python3
"""
Status Reporter - Puddle Assistant
Genera reportes del estado de procesamiento de documentos
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class StatusReporter:
    """Generador de reportes de estado."""
    
    def __init__(self,
                 input_path: str = "data/raw/documents",
                 output_path: str = "data/processed/DocsMD", 
                 status_file: str = "logs/processing_status.json",
                 reports_path: str = "logs"):
        
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.status_file = Path(status_file)
        self.reports_path = Path(reports_path)
        
        self.supported_extensions = {'.pdf', '.docx', '.doc', '.pptx'}
        
        # Crear directorio de reportes
        self.reports_path.mkdir(parents=True, exist_ok=True)
    
    def load_status(self) -> Dict:
        """Carga el estado de procesamiento."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error cargando estado: {e}")
        
        return {"processed_files": {}, "stats": {"successful": 0, "failed": 0}}
    
    def get_input_files(self) -> List[Path]:
        """Obtiene archivos de entrada."""
        if not self.input_path.exists():
            return []
        
        return [f for f in self.input_path.iterdir() 
                if f.is_file() and f.suffix.lower() in self.supported_extensions]
    
    def get_output_files(self) -> List[Path]:
        """Obtiene archivos Markdown generados."""
        if not self.output_path.exists():
            return []
        
        return list(self.output_path.glob('*.md'))
    
    def generate_table_data(self) -> List[Dict]:
        """Genera datos para la tabla de estado."""
        status_data = self.load_status()
        input_files = self.get_input_files()
        
        table_data = []
        
        for file_path in sorted(input_files):
            file_info = status_data["processed_files"].get(file_path.name, {})
            
            # Archivo MD esperado
            expected_md = self.output_path / f"{file_path.stem}.md"
            md_exists = expected_md.exists()
            
            # Información del archivo original
            original_size_kb = file_path.stat().st_size / 1024
            
            # Información del archivo MD
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
                "documento_original": file_path.name,
                "tamaño_original_kb": round(original_size_kb, 1),
                "archivo_markdown": expected_md.name if md_exists else "N/A",
                "md_generado": "✅ Sí" if md_exists else "❌ No",
                "tamaño_md_kb": round(md_size_kb, 1) if md_exists else 0.0,
                "caracteres_md": f"{md_chars:,}" if md_chars > 0 else "0",
                "estado": "✅ Completado" if md_exists else "⏳ Pendiente",
                "procesado_en": file_info.get("processed_at", "N/A"),
                "error": file_info.get("error", "")[:100] if file_info.get("error") else ""
            }
            
            table_data.append(row)
        
        return table_data
    
    def generate_statistics(self) -> Dict:
        """Genera estadísticas del procesamiento."""
        status_data = self.load_status()
        input_files = self.get_input_files()
        output_files = self.get_output_files()
        
        # Contar archivos procesados exitosamente
        processed_count = len([f for f in input_files 
                              if (self.output_path / f"{f.stem}.md").exists()])
        
        # Calcular tamaños
        total_original_mb = sum(f.stat().st_size for f in input_files) / (1024*1024)
        total_md_mb = sum(f.stat().st_size for f in output_files) / (1024*1024)
        
        reduction_pct = 0
        if total_original_mb > 0:
            reduction_pct = ((total_original_mb - total_md_mb) / total_original_mb) * 100
        
        return {
            "total_documents": len(input_files),
            "processed_documents": processed_count,
            "pending_documents": len(input_files) - processed_count,
            "completion_percentage": (processed_count / len(input_files)) * 100 if input_files else 0,
            "md_files_count": len(output_files),
            "total_original_mb": round(total_original_mb, 1),
            "total_md_mb": round(total_md_mb, 1),
            "size_reduction_pct": round(reduction_pct, 1),
            "successful_count": status_data["stats"]["successful"],
            "failed_count": status_data["stats"]["failed"],
            "last_update": status_data.get("last_update", "N/A")
        }
    
    def print_summary_report(self):
        """Imprime reporte resumido en consola."""
        print("📋 REPORTE DE ESTADO - PUDDLE ASSISTANT")
        print("=" * 60)
        
        stats = self.generate_statistics()
        
        print(f"\n📊 ESTADÍSTICAS GENERALES:")
        print(f"  📄 Total documentos: {stats['total_documents']}")
        print(f"  ✅ Procesados: {stats['processed_documents']}")
        print(f"  ⏳ Pendientes: {stats['pending_documents']}")
        print(f"  📈 Completado: {stats['completion_percentage']:.1f}%")
        print(f"  📁 Archivos MD: {stats['md_files_count']}")
        
        print(f"\n💾 TAMAÑOS:")
        print(f"  📄 Total original: {stats['total_original_mb']} MB")
        print(f"  📝 Total Markdown: {stats['total_md_mb']} MB")
        print(f"  📉 Reducción: {stats['size_reduction_pct']}%")
        
        print(f"\n🔄 PROCESAMIENTO:")
        print(f"  ✅ Exitosos: {stats['successful_count']}")
        print(f"  ❌ Fallidos: {stats['failed_count']}")
        print(f"  📅 Última actualización: {stats['last_update'][:19] if stats['last_update'] != 'N/A' else 'N/A'}")
    
    def generate_detailed_table(self, save_csv: bool = True) -> pd.DataFrame:
        """Genera tabla detallada."""
        table_data = self.generate_table_data()
        
        if not table_data:
            print("❌ No hay datos para generar tabla")
            return pd.DataFrame()
        
        df = pd.DataFrame(table_data)
        
        # Mostrar tabla en consola
        print(f"\n📋 TABLA DETALLADA:")
        print("-" * 80)
        
        # Versión simplificada para consola
        display_cols = ["documento_original", "md_generado", "tamaño_md_kb", "estado"]
        print(df[display_cols].to_string(index=False))
        
        # Guardar CSV si se solicita
        if save_csv:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = self.reports_path / f"status_report_{timestamp}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"\n💾 Tabla detallada guardada: {csv_path}")
        
        return df
    
    def list_output_files(self):
        """Lista archivos Markdown generados."""
        md_files = sorted(self.get_output_files())
        
        print(f"\n📁 ARCHIVOS MARKDOWN GENERADOS:")
        print("-" * 50)
        
        if md_files:
            for md_file in md_files:
                size_kb = md_file.stat().st_size / 1024
                print(f"  📄 {md_file.name} ({size_kb:.1f} KB)")
        else:
            print("  (No hay archivos Markdown)")


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generador de reportes de estado")
    parser.add_argument("--summary", action="store_true", help="Mostrar solo resumen")
    parser.add_argument("--table", action="store_true", help="Mostrar tabla detallada")
    parser.add_argument("--files", action="store_true", help="Listar archivos generados")
    parser.add_argument("--all", action="store_true", help="Mostrar todo")
    parser.add_argument("--no-csv", action="store_true", help="No guardar CSV")
    
    args = parser.parse_args()
    
    reporter = StatusReporter()
    
    if args.all or not any([args.summary, args.table, args.files]):
        # Mostrar todo por defecto
        reporter.print_summary_report()
        reporter.generate_detailed_table(save_csv=not args.no_csv)
        reporter.list_output_files()
        
    else:
        if args.summary:
            reporter.print_summary_report()
        
        if args.table:
            reporter.generate_detailed_table(save_csv=not args.no_csv)
        
        if args.files:
            reporter.list_output_files()


if __name__ == "__main__":
    main()