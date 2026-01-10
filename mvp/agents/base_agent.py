#!/usr/bin/env python3
"""
Base Agent - MVP System
Clase base para todos los agentes del sistema
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Estado compartido entre agentes."""
    user_input: str
    language: Optional[str] = None
    language_config: Optional[Dict] = None
    mode: Optional[str] = None
    mode_confidence: Optional[float] = None
    context: Optional[str] = None
    response: Optional[str] = None
    sources: Optional[list] = None
    metadata: Optional[Dict] = None
    debug_info: Optional[Dict] = None

class BaseAgent(ABC):
    """Agente base con funcionalidades comunes."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """
        Procesa el estado y retorna el estado actualizado.
        
        Args:
            state: Estado actual del sistema
            
        Returns:
            Estado actualizado después del procesamiento
        """
        pass
    
    def should_process(self, state: AgentState) -> bool:
        """
        Determina si este agente debe procesar el estado actual.
        Por defecto, siempre procesa.
        
        Args:
            state: Estado actual
            
        Returns:
            True si debe procesar, False en caso contrario
        """
        return True
    
    def log_processing(self, state: AgentState, action: str):
        """Helper para logging consistente."""
        self.logger.info(f"🤖 {self.name}: {action}")
    
    def add_debug_info(self, state: AgentState, key: str, value: Any):
        """Agrega información de debug al estado."""
        if state.debug_info is None:
            state.debug_info = {}
        if self.name not in state.debug_info:
            state.debug_info[self.name] = {}
        state.debug_info[self.name][key] = value