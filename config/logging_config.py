"""
Configuración de logging para Puddle Assistant
"""

import logging
import logging.config
from pathlib import Path

# Crear directorio de logs si no existe
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file_info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': str(LOG_DIR / 'app.log'),
            'mode': 'a',
            'encoding': 'utf-8'
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'detailed',
            'filename': str(LOG_DIR / 'debug.log'),
            'mode': 'a',
            'encoding': 'utf-8'
        },
        'processing_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': str(LOG_DIR / 'processing.log'),
            'mode': 'a',
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        'document_processor': {
            'handlers': ['console', 'processing_file'],
            'level': 'INFO',
            'propagate': False
        },
        'status_reporter': {
            'handlers': ['console', 'file_info'],
            'level': 'INFO',
            'propagate': False
        },
        'rag_assistant': {
            'handlers': ['console', 'file_info'],
            'level': 'INFO',
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file_info']
    }
}

def setup_logging():
    """Configura el sistema de logging."""
    logging.config.dictConfig(LOGGING_CONFIG)

def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger configurado."""
    setup_logging()
    return logging.getLogger(name)