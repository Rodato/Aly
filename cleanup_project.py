#!/usr/bin/env python3
"""
PUDDLE ASSISTANT - Script de Limpieza Automática
=================================================
Elimina archivos temporales, logs, cache y bases de datos locales
antes de hacer commit/push a GitHub.

USO:
    python3 cleanup_project.py --dry-run  # Ver qué se eliminará
    python3 cleanup_project.py            # Ejecutar limpieza real
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import List, Tuple

# Colores para output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def get_dir_size(path: Path) -> int:
    """Calcula el tamaño total de un directorio."""
    total = 0
    try:
        if path.is_file():
            return path.stat().st_size
        for item in path.rglob('*'):
            if item.is_file():
                try:
                    total += item.stat().st_size
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass
    return total

def format_size(size_bytes: int) -> str:
    """Convierte bytes a formato legible."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def find_items_to_clean(base_path: Path) -> dict:
    """Identifica todos los archivos/directorios a limpiar."""
    items = {
        'python_cache': [],
        'logs': [],
        'databases': [],
        'embeddings': [],
        'backups': [],
        'system_files': [],
        'node_modules': [],
        'venv': []
    }

    # Python Cache (__pycache__)
    for pycache in base_path.rglob('__pycache__'):
        if 'venv' not in str(pycache):  # Excluir dentro de venv
            items['python_cache'].append(pycache)

    # Archivos .pyc, .pyo
    for pattern in ['**/*.pyc', '**/*.pyo', '**/*.pyd']:
        for file in base_path.glob(pattern):
            if 'venv' not in str(file):
                items['python_cache'].append(file)

    # Logs
    logs_dir = base_path / 'logs'
    if logs_dir.exists():
        items['logs'].append(logs_dir)

    for log_file in base_path.rglob('*.log'):
        if 'venv' not in str(log_file):
            items['logs'].append(log_file)

    nohup = base_path / 'nohup.out'
    if nohup.exists():
        items['logs'].append(nohup)

    # Bases de datos locales
    chroma_db = base_path / 'data' / 'chroma_db'
    if chroma_db.exists():
        items['databases'].append(chroma_db)

    for db_file in base_path.rglob('*.db'):
        if 'venv' not in str(db_file) and 'node_modules' not in str(db_file):
            items['databases'].append(db_file)

    for sqlite_file in base_path.rglob('*.sqlite*'):
        if 'venv' not in str(sqlite_file) and 'node_modules' not in str(sqlite_file):
            items['databases'].append(sqlite_file)

    # Embeddings
    embeddings_dir = base_path / 'data' / 'processed' / 'embeddings'
    if embeddings_dir.exists():
        items['embeddings'].append(embeddings_dir)

    # Backups
    backups_dir = base_path / 'data' / 'processed' / 'backups'
    if backups_dir.exists():
        items['backups'].append(backups_dir)

    # System files
    for ds_store in base_path.rglob('.DS_Store'):
        items['system_files'].append(ds_store)

    rhistory = base_path / '.Rhistory'
    if rhistory.exists():
        items['system_files'].append(rhistory)

    # Node modules (opcional, solo mostrar)
    for node_modules in base_path.rglob('node_modules'):
        if node_modules.is_dir():
            items['node_modules'].append(node_modules)

    # Venv (opcional, solo mostrar)
    venv_dir = base_path / 'venv'
    if venv_dir.exists():
        items['venv'].append(venv_dir)

    return items

def clean_items(items: dict, dry_run: bool = False) -> Tuple[int, int]:
    """Elimina los items identificados."""
    total_size = 0
    total_count = 0

    categories = {
        'python_cache': '🐍 Python Cache',
        'logs': '📋 Logs',
        'databases': '🗄️  Bases de datos locales',
        'embeddings': '🧠 Embeddings',
        'backups': '💾 Backups',
        'system_files': '🖥️  Archivos de sistema',
    }

    for category, label in categories.items():
        if not items[category]:
            continue

        print(f"\n{Colors.CYAN}{Colors.BOLD}{label}{Colors.RESET}")
        print("-" * 60)

        for item in items[category]:
            if not item.exists():
                continue

            size = get_dir_size(item)
            total_size += size
            total_count += 1

            rel_path = item.relative_to(Path.cwd())
            size_str = format_size(size)

            if dry_run:
                print(f"  {Colors.YELLOW}[DRY RUN]{Colors.RESET} {rel_path} ({size_str})")
            else:
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    print(f"  {Colors.GREEN}✓{Colors.RESET} Eliminado: {rel_path} ({size_str})")
                except Exception as e:
                    print(f"  {Colors.RED}✗{Colors.RESET} Error: {rel_path} - {e}")

    return total_count, total_size

def show_info_items(items: dict):
    """Muestra información sobre items que NO se eliminan."""
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}ℹ️  Items NO eliminados (opcional manual){Colors.RESET}")
    print("-" * 60)

    # Node modules
    if items['node_modules']:
        total_size = sum(get_dir_size(p) for p in items['node_modules'])
        print(f"\n  {Colors.BLUE}📦 node_modules{Colors.RESET} ({len(items['node_modules'])} directorios)")
        for nm in items['node_modules']:
            size = get_dir_size(nm)
            rel_path = nm.relative_to(Path.cwd())
            print(f"     - {rel_path} ({format_size(size)})")
        print(f"     {Colors.YELLOW}Total: {format_size(total_size)}{Colors.RESET}")
        print(f"     Tip: Regenerar con 'npm install'")

    # Venv
    if items['venv']:
        total_size = sum(get_dir_size(p) for p in items['venv'])
        print(f"\n  {Colors.BLUE}🐍 venv{Colors.RESET} ({len(items['venv'])} directorios)")
        for venv in items['venv']:
            size = get_dir_size(venv)
            rel_path = venv.relative_to(Path.cwd())
            print(f"     - {rel_path} ({format_size(size)})")
        print(f"     {Colors.YELLOW}Total: {format_size(total_size)}{Colors.RESET}")
        print(f"     Tip: Regenerar con 'python3 -m venv venv && pip install -r requirements.txt'")

def main():
    parser = argparse.ArgumentParser(
        description='Limpia archivos temporales del proyecto Puddle Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python3 cleanup_project.py --dry-run    # Ver qué se eliminará sin hacer cambios
  python3 cleanup_project.py              # Ejecutar limpieza real
  python3 cleanup_project.py --all        # Incluir venv y node_modules (¡CUIDADO!)
        """
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mostrar qué se eliminaría sin hacer cambios reales'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Incluir venv y node_modules (¡regenerables pero tardados!)'
    )

    args = parser.parse_args()

    # Header
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  PUDDLE ASSISTANT - Script de Limpieza{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    if args.dry_run:
        print(f"{Colors.YELLOW}Modo DRY RUN: No se eliminarán archivos reales{Colors.RESET}\n")

    # Buscar items
    print(f"{Colors.BLUE}Escaneando proyecto...{Colors.RESET}")
    base_path = Path.cwd()
    items = find_items_to_clean(base_path)

    # Limpiar
    total_count, total_size = clean_items(items, dry_run=args.dry_run)

    # Mostrar info items opcionales
    show_info_items(items)

    # Resumen
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}RESUMEN{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}")

    if args.dry_run:
        print(f"  Items que se eliminarían: {total_count}")
        print(f"  Espacio que se liberaría: {Colors.BOLD}{format_size(total_size)}{Colors.RESET}")
        print(f"\n  {Colors.YELLOW}Para ejecutar la limpieza real, quita el flag --dry-run{Colors.RESET}")
    else:
        print(f"  Items eliminados: {Colors.GREEN}{total_count}{Colors.RESET}")
        print(f"  Espacio liberado: {Colors.BOLD}{Colors.GREEN}{format_size(total_size)}{Colors.RESET}")
        print(f"\n  {Colors.GREEN}✓ Limpieza completada exitosamente{Colors.RESET}")

    print()

if __name__ == "__main__":
    main()
