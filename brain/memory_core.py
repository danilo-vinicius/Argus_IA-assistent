import os
import shutil
import time
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ==========================================
# 🧠 CONFIGURAÇÃO DA MEMÓRIA (CORTEX)
# ==========================================
KNOWLEDGE_DIR = "knowledge_base"
PROCESSED_DIR = os.path.join(KNOWLEDGE_DIR, "documentos_lidos") 
DB_DIR = "chroma_db_permanent" 

EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def aprender_documentos():
    """
    Lê arquivos, valida conteúdo, salva na memória e arquiva.
    """
    print(f"🧠 [MEMÓRIA] Verificando Caixa de Entrada '{KNOWLEDGE_DIR}'...")
    
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

    # 1. Carregadores
    loaders = [
        DirectoryLoader(KNOWLEDGE_DIR, glob="*.pdf", loader_cls=PyMuPDFLoader),
        DirectoryLoader(KNOWLEDGE_DIR, glob="*.txt", loader_cls=TextLoader)
    ]
    
    documents = []
    files_found = []

    for loader in loaders:
        try:
            docs = loader.load()
            for doc in docs:
                # --- NOVO: FILTRO DE CONTEÚDO VAZIO ---
                if doc.page_content and len(doc.page_content.strip()) > 10:
                    documents.append(doc)
                    source = doc.metadata.get('source')
                    if source and source not in files_found:
                        files_found.append(source)
                else:
                    print(f"⚠️ Aviso: Página vazia ou imagem ignorada em: {doc.metadata.get('source')}")
                    
        except Exception as e:
            print(f"⚠️ Erro ao ler arquivo: {e}")

    if not documents:
        print("✅ Nenhum texto válido encontrado para processar.")
        return

    print(f"📚 [MEMÓRIA] Processando {len(files_found)} arquivos com texto legível...")

    # 2. Quebrar em Pedaços
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    
    # --- NOVO: VERIFICAÇÃO FINAL ANTES DO BANCO ---
    if not chunks:
        print("❌ Erro: O processamento gerou 0 fragmentos. Os arquivos podem ser imagens/scans.")
        return

    print(f"🧩 [MEMÓRIA] Gerando {len(chunks)} fragmentos neurais...")

    # 3. Salvar no ChromaDB
    try:
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=EMBEDDING_MODEL,
            persist_directory=DB_DIR
        )
        print("💾 [SUCESSO] Conhecimento gravado no Córtex!")
        
        # 4. ARQUIVAMENTO
        print("📦 [ORGANIZAÇÃO] Arquivando documentos...")
        
        for file_path in files_found:
            try:
                file_name = os.path.basename(file_path)
                destination = os.path.join(PROCESSED_DIR, file_name)
                
                if os.path.exists(destination):
                    timestamp = int(time.time())
                    name, ext = os.path.splitext(file_name)
                    destination = os.path.join(PROCESSED_DIR, f"{name}_{timestamp}{ext}")
                
                shutil.move(file_path, destination)
                print(f"   -> Movido: {file_name}")
                
            except Exception as move_err:
                print(f"   ⚠️ Erro ao mover {file_name}: {move_err}")
        
    except Exception as e:
        print(f"❌ Erro Crítico ao gravar no banco: {e}")

def buscar_memoria(query, k=3):
    if not os.path.exists(DB_DIR):
        return []

    vector_db = Chroma(persist_directory=DB_DIR, embedding_function=EMBEDDING_MODEL)
    results = vector_db.similarity_search(query, k=k)
    return results

if __name__ == "__main__":
    print("--- INICIANDO ROTINA DE APRENDIZADO ---")
    aprender_documentos()