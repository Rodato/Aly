#!/usr/bin/env python3
"""
Agent Console - MVP System
Interfaz de consola para probar el sistema de agentes
"""

import sys
import os

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_orchestrator import AgentOrchestrator

def main():
    """Consola interactiva del sistema de agentes."""
    
    print("🚀 INICIALIZANDO SISTEMA DE AGENTES MVP ALY...")
    print("=" * 70)
    
    try:
        orchestrator = AgentOrchestrator()
        print("✅ Sistema de agentes inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando sistema: {e}")
        return
    
    print("\n" + "="*70)
    print("🤖 SISTEMA DE AGENTES MVP ALY")
    print("🧠 Detección automática de idioma (ES/EN/PT)")
    print("🎯 Detección inteligente de intención:")
    print("   📚 FACTUAL: Consultas sobre conocimiento específico")
    print("   📋 PLAN: Adaptar/implementar actividades conocidas")
    print("   💡 IDEATE: Nuevas ideas creativas y variaciones")
    print("   ⚠️ SENSITIVE: Temas sensibles con orientación segura")
    print("   ❓ AMBIGUOUS: Clarificación de inputs poco claros")
    print("💡 Escribe tu consulta en cualquier idioma")
    print("Escribe 'salir' para terminar")
    print("="*70)
    
    session_started = False
    
    while True:
        try:
            query = input("\n🔍 Tu consulta: ").strip()
            
            # Comandos de salida
            if not query:
                print("💡 Escribe tu consulta o 'salir' para terminar.")
                continue
                
            if query.lower() in ['salir', 'exit', 'quit', 'sair']:
                print("\n👋 ¡Hasta luego! / Goodbye! / Tchau!")
                break
            
            print("\n⏳ Procesando con sistema de agentes...")
            
            # Procesar consulta
            result = orchestrator.process_query(query, debug=True)
            
            # Mostrar saludo inicial si es primera consulta
            if not session_started:
                greeting = orchestrator.get_session_greeting(query)
                print(f"\n👋 {greeting}")
                session_started = True
            
            # Mostrar información de detección
            lang_flag = '🇪🇸' if result['language'] == 'es' else '🇺🇸' if result['language'] == 'en' else '🇧🇷'
            
            # Map intent to emoji
            intent_emoji_map = {
                'FACTUAL': '📚',
                'PLAN': '📋', 
                'IDEATE': '💡',
                'SENSITIVE': '⚠️',
                'AMBIGUOUS': '❓',
                'error': '❌'
            }
            intent = result.get('intent', 'error')
            intent_emoji = intent_emoji_map.get(intent, '🤖')
            
            print(f"\n🌍 Idioma: {lang_flag} {result['language_name']}")
            print(f"{intent_emoji} Intent: {intent} (confianza: {result.get('intent_confidence', 0.0):.2f})")
            if 'agent_type' in result:
                print(f"🤖 Agente: {result['agent_type']}")
            
            # Mostrar respuesta (formato conversacional natural)
            print(f"\n{result['answer']}")
            
            # TODO: Descomentar si se necesitan fuentes y debug info en el futuro
            # # Mostrar fuentes si las hay
            # if result['sources']:
            #     print(f"\n📚 **Fuentes consultadas ({len(result['sources'])}):**")
            #     for i, source in enumerate(result['sources'], 1):
            #         print(f"  {i}. **{source['document'][:50]}...**")
            #         print(f"     📝 Sección: {source['section']}")
            #         print(f"     🎯 Similitud: {source['similarity']}")
            # 
            # # Debug info (opcional)
            # if 'debug_info' in result and result['debug_info']:
            #     print(f"\n🔧 **Debug Info:**")
            #     for agent, info in result['debug_info'].items():
            #         print(f"   🤖 {agent}: {info}")
            
            print("\n" + "-"*60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrumpido por usuario")
            break
        except Exception as e:
            print(f"\n❌ Error procesando consulta: {e}")
            continue

if __name__ == "__main__":
    main()