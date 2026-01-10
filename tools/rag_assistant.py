import os
from typing import List, Any
from dotenv import load_dotenv
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_core.language_models import BaseLanguageModel
from langchain.chains.retrieval_qa import RetrievalQA
from pydantic import Field
import requests
import json

load_dotenv()

class OpenRouterLLM(BaseLanguageModel):
    model_name: str = "mistralai/ministral-8b"
    openrouter_api_key: str = ""
    max_tokens: int = 1000
    temperature: float = 0.1
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada en variables de entorno")
    
    @property
    def _llm_type(self) -> str:
        return "openrouter"
    
    def _call(self, prompt: str, stop: List[str] = None, **kwargs: Any) -> str:
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error al conectar con OpenRouter: {str(e)}"

class OpenRouterEmbeddings:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada en variables de entorno")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embedding = self._get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        return self._get_embedding(text)
    
    def _get_embedding(self, text: str) -> List[float]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "openai/text-embedding-ada-002",
            "input": text
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result["data"][0]["embedding"]
        except Exception as e:
            print(f"Error al obtener embedding: {str(e)}")
            return [0.0] * 1536

class RAGAssistant:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = OpenRouterEmbeddings()
        self.llm = OpenRouterLLM()
        self.vectorstore = None
        self.qa_chain = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
    
    def load_documents(self, documents_path: str = "./documents"):
        documents = []
        
        for filename in os.listdir(documents_path):
            file_path = os.path.join(documents_path, filename)
            
            if filename.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                documents.extend(docs)
            elif filename.endswith('.txt'):
                loader = TextLoader(file_path, encoding='utf-8')
                docs = loader.load()
                documents.extend(docs)
        
        if not documents:
            raise ValueError("No se encontraron documentos para procesar")
        
        texts = self.text_splitter.split_documents(documents)
        return texts
    
    def create_vectorstore(self, documents_path: str = "./documents"):
        texts = self.load_documents(documents_path)
        
        self.vectorstore = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        self.vectorstore.persist()
        print(f"Base de datos vectorial creada con {len(texts)} documentos")
    
    def create_vectorstore_from_markdown(self, markdown_path: str = "./markdown_docs"):
        """Crea base de datos vectorial desde archivos markdown."""
        
        # Cargar todos los archivos markdown
        loader = DirectoryLoader(
            markdown_path, 
            glob="*.md",
            loader_cls=TextLoader,
            loader_kwargs={'encoding': 'utf-8'}
        )
        
        documents = loader.load()
        
        if not documents:
            raise ValueError("No se encontraron archivos markdown para procesar")
        
        # Dividir documentos en chunks
        texts = self.text_splitter.split_documents(documents)
        
        # Crear base de datos vectorial
        self.vectorstore = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        self.vectorstore.persist()
        print(f"Base de datos vectorial creada con {len(texts)} chunks desde {len(documents)} documentos markdown")
    
    def load_vectorstore(self):
        if os.path.exists(self.persist_directory):
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print("Base de datos vectorial cargada exitosamente")
        else:
            raise ValueError("No existe una base de datos vectorial. Ejecuta create_vectorstore() primero")
    
    def setup_qa_chain(self):
        if not self.vectorstore:
            self.load_vectorstore()
        
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
    
    def query(self, question: str):
        if not self.qa_chain:
            self.setup_qa_chain()
        
        try:
            result = self.qa_chain({"query": question})
            return {
                "answer": result["result"],
                "source_documents": result["source_documents"]
            }
        except Exception as e:
            return {
                "answer": f"Error al procesar la consulta: {str(e)}",
                "source_documents": []
            }
    
    def add_document(self, file_path: str):
        if not self.vectorstore:
            self.load_vectorstore()
        
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.txt'):
            loader = TextLoader(file_path, encoding='utf-8')
        else:
            raise ValueError("Solo se admiten archivos PDF y TXT")
        
        documents = loader.load()
        texts = self.text_splitter.split_documents(documents)
        
        self.vectorstore.add_documents(texts)
        self.vectorstore.persist()
        
        print(f"Documento agregado: {file_path}")