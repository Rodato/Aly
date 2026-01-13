#!/usr/bin/env python3
"""
Filter Detection Agent - MVP System
Detecta menciones a programas, categorías y audiencias para filtrar búsquedas
"""

import os
import json
import re
from typing import Dict, List, Optional
from .base_agent import BaseAgent, AgentState

class FilterDetectionAgent(BaseAgent):
    """
    Agente que detecta menciones a programas, documentos o categorías específicas
    para optimizar la búsqueda en MongoDB.
    """

    def __init__(self):
        super().__init__(
            name="filter_detection_agent",
            description="Detecta menciones a programas/documentos específicos para filtrar búsquedas"
        )

        # Cargar catálogo de programas
        self.program_catalog = self._load_program_catalog()

        # Definir categorías conocidas
        self.categories = {
            'curriculum': ['curriculum', 'currículo', 'curriculo'],
            'manual': ['manual', 'handbook'],
            'guide': ['guide', 'guía', 'guia'],
            'brief': ['brief', 'resumen'],
            'toolkit': ['toolkit', 'herramientas'],
            'report': ['report', 'reporte', 'informe'],
            'resource': ['resource', 'recurso']
        }

        # Definir audiencias conocidas
        self.audiences = {
            'fathers': ['fathers', 'padres', 'pais'],
            'mothers': ['mothers', 'madres', 'mães'],
            'parents': ['parents', 'parenting'],
            'youth': ['youth', 'jóvenes', 'jovens', 'adolescentes', 'adolescents'],
            'boys': ['boys', 'niños', 'meninos'],
            'girls': ['girls', 'niñas', 'meninas'],
            'men': ['men', 'hombres', 'homens'],
            'women': ['women', 'mujeres', 'mulheres'],
            'educators': ['educators', 'educadores', 'teachers', 'maestros', 'facilitators', 'facilitadores'],
        }

        self.logger.info(f"✅ Filter Detection Agent inicializado con {len(self.program_catalog)} programas")

    def _load_program_catalog(self) -> Dict:
        """Carga el catálogo de programas desde JSON."""

        catalog_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..',
            'mongodb', 'scripts',
            'program_catalog.json'
        )

        try:
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
            self.logger.info(f"📚 Catálogo cargado: {len(catalog)} programas")
            return catalog
        except Exception as e:
            self.logger.warning(f"⚠️ Error cargando catálogo: {e}")
            return {}

    def process(self, state: AgentState) -> AgentState:
        """Detecta filtros en el input del usuario."""

        self.log_processing(state, f"Detectando filtros en: '{state.user_input[:50]}...'")

        user_input_lower = state.user_input.lower()

        # Detectar programas
        detected_programs = self._detect_programs(user_input_lower)

        # Detectar categorías
        detected_categories = self._detect_categories(user_input_lower)

        # Detectar audiencias
        detected_audiences = self._detect_audiences(user_input_lower)

        # Construir filtros MongoDB
        filters = self._build_mongodb_filters(
            detected_programs,
            detected_categories,
            detected_audiences
        )

        # Guardar en metadata
        if not state.metadata:
            state.metadata = {}

        state.metadata['detected_filters'] = {
            'programs': detected_programs,
            'categories': detected_categories,
            'audiences': detected_audiences,
            'mongodb_filters': filters,
            'has_filters': len(filters) > 0
        }

        # Debug info
        if filters:
            self.log_processing(state, f"Filtros detectados: {filters}")
            self.add_debug_info(state, "filters_detected", filters)
            self.add_debug_info(state, "programs_detected", detected_programs)
            self.add_debug_info(state, "categories_detected", detected_categories)
            self.add_debug_info(state, "audiences_detected", detected_audiences)
        else:
            self.log_processing(state, "No se detectaron filtros específicos")
            self.add_debug_info(state, "filters_detected", None)

        return state

    def _detect_programs(self, user_input: str) -> List[str]:
        """Detecta menciones a programas usando aliases."""

        detected = []

        for program_id, program_data in self.program_catalog.items():
            aliases = program_data.get('aliases', [])

            for alias in aliases:
                # Buscar el alias como palabra completa (con word boundaries)
                pattern = r'\b' + re.escape(alias.lower()) + r'\b'

                if re.search(pattern, user_input):
                    detected.append(program_id)
                    self.logger.info(f"🎯 Programa detectado: {program_id} (alias: '{alias}')")
                    break  # Solo agregar una vez por programa

        return detected

    def _detect_categories(self, user_input: str) -> List[str]:
        """Detecta menciones a categorías de documentos."""

        detected = []

        for category, keywords in self.categories.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'

                if re.search(pattern, user_input):
                    detected.append(category)
                    self.logger.info(f"📑 Categoría detectada: {category}")
                    break

        return detected

    def _detect_audiences(self, user_input: str) -> List[str]:
        """Detecta menciones a audiencias objetivo."""

        detected = []

        for audience, keywords in self.audiences.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'

                if re.search(pattern, user_input):
                    detected.append(audience)
                    self.logger.info(f"👥 Audiencia detectada: {audience}")
                    break

        return detected

    def _build_mongodb_filters(
        self,
        programs: List[str],
        categories: List[str],
        audiences: List[str]
    ) -> Dict:
        """Construye filtros para MongoDB."""

        filters = {}

        # Filtro de programa (OR entre múltiples programas)
        if programs:
            if len(programs) == 1:
                filters['program_name'] = programs[0]
            else:
                filters['program_name'] = {'$in': programs}

        # Filtro de categoría (OR entre múltiples categorías)
        if categories:
            if len(categories) == 1:
                filters['document_category'] = categories[0]
            else:
                filters['document_category'] = {'$in': categories}

        # Filtro de audiencia (debe incluir al menos una de las audiencias)
        if audiences:
            if len(audiences) == 1:
                filters['target_audiences'] = audiences[0]
            else:
                filters['target_audiences'] = {'$in': audiences}

        return filters

    def get_filter_summary(self, state: AgentState) -> Optional[str]:
        """Genera un resumen legible de los filtros detectados."""

        if not state.metadata or 'detected_filters' not in state.metadata:
            return None

        filters_info = state.metadata['detected_filters']

        if not filters_info['has_filters']:
            return None

        summary_parts = []

        if filters_info['programs']:
            prog_names = [self.program_catalog[p]['full_name'] for p in filters_info['programs'] if p in self.program_catalog]
            summary_parts.append(f"Programa(s): {', '.join(prog_names)}")

        if filters_info['categories']:
            summary_parts.append(f"Tipo: {', '.join(filters_info['categories'])}")

        if filters_info['audiences']:
            summary_parts.append(f"Audiencia: {', '.join(filters_info['audiences'])}")

        return " | ".join(summary_parts) if summary_parts else None
