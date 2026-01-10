import streamlit as st
import os
import shutil
from rag_assistant import RAGAssistant

st.set_page_config(
    page_title="Puddle Assistant - RAG",
    page_icon="🤖",
    layout="wide"
)

def initialize_assistant():
    if 'assistant' not in st.session_state:
        st.session_state.assistant = RAGAssistant()
        st.session_state.vectorstore_ready = False

def check_vectorstore():
    return os.path.exists("./chroma_db")

def main():
    st.title("🤖 Puddle Assistant - RAG")
    st.markdown("### Asistente Inteligente con Recuperación de Información")
    
    initialize_assistant()
    
    with st.sidebar:
        st.header("📁 Gestión de Documentos")
        
        if not check_vectorstore():
            st.warning("⚠️ Base de datos vectorial no encontrada")
            st.info("Sube documentos y haz clic en 'Crear Base de Datos' para comenzar")
        else:
            st.success("✅ Base de datos vectorial lista")
            st.session_state.vectorstore_ready = True
        
        uploaded_files = st.file_uploader(
            "Subir documentos (PDF/TXT)",
            accept_multiple_files=True,
            type=['pdf', 'txt']
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = os.path.join("./documents", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"✅ {uploaded_file.name} guardado")
        
        documents_in_folder = []
        if os.path.exists("./documents"):
            documents_in_folder = [f for f in os.listdir("./documents") 
                                 if f.endswith(('.pdf', '.txt'))]
        
        if documents_in_folder:
            st.write("📋 **Documentos disponibles:**")
            for doc in documents_in_folder:
                st.write(f"- {doc}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Crear Base de Datos", type="primary"):
                    with st.spinner("Procesando documentos..."):
                        try:
                            st.session_state.assistant.create_vectorstore("./documents")
                            st.session_state.vectorstore_ready = True
                            st.success("✅ Base de datos creada exitosamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            
            with col2:
                if st.button("🗑️ Limpiar Todo"):
                    if os.path.exists("./chroma_db"):
                        shutil.rmtree("./chroma_db")
                    if os.path.exists("./documents"):
                        for file in os.listdir("./documents"):
                            os.remove(os.path.join("./documents", file))
                    st.session_state.vectorstore_ready = False
                    st.success("✅ Todo limpiado")
                    st.rerun()
        
        st.divider()
        st.markdown("""
        ### 📖 Cómo usar:
        1. Sube tus documentos (PDF/TXT)
        2. Haz clic en "Crear Base de Datos"
        3. Realiza preguntas sobre el contenido
        """)
    
    if st.session_state.vectorstore_ready or check_vectorstore():
        st.header("💬 Chat con tus documentos")
        
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and "sources" in message:
                    with st.expander("📄 Ver fuentes"):
                        for i, source in enumerate(message["sources"]):
                            st.write(f"**Fuente {i+1}:**")
                            st.write(source.page_content[:300] + "...")
                            if hasattr(source, 'metadata') and 'source' in source.metadata:
                                st.write(f"*Archivo: {source.metadata['source']}*")
                            st.divider()
        
        if prompt := st.chat_input("Pregúntame sobre tus documentos..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Buscando en documentos..."):
                    try:
                        result = st.session_state.assistant.query(prompt)
                        answer = result["answer"]
                        sources = result["source_documents"]
                        
                        st.markdown(answer)
                        
                        if sources:
                            with st.expander("📄 Ver fuentes"):
                                for i, source in enumerate(sources):
                                    st.write(f"**Fuente {i+1}:**")
                                    st.write(source.page_content[:300] + "...")
                                    if hasattr(source, 'metadata') and 'source' in source.metadata:
                                        st.write(f"*Archivo: {source.metadata['source']}*")
                                    st.divider()
                        
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": answer,
                            "sources": sources
                        })
                    
                    except Exception as e:
                        error_msg = f"❌ Error al procesar la consulta: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": error_msg
                        })
    
    else:
        st.info("👆 Sube algunos documentos en la barra lateral para comenzar")
        
        st.markdown("""
        ## 🚀 Bienvenido a Puddle Assistant
        
        Este asistente inteligente te permite:
        - 📄 Subir documentos PDF y TXT
        - 🔍 Hacer preguntas sobre el contenido
        - 💡 Obtener respuestas contextualmente relevantes
        - 📋 Ver las fuentes de información
        
        ### 🛠️ Tecnologías utilizadas:
        - **LangChain** para el pipeline RAG
        - **OpenRouter** para LLM (ministral-8b) y embeddings (text-embedding-ada-002)
        - **ChromaDB** para almacenamiento vectorial
        - **Streamlit** para la interfaz web
        """)

if __name__ == "__main__":
    main()