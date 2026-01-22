import os
import time
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import shutil

# --- CONFIGURAÇÃO ---
embeddings = OllamaEmbeddings(model="nomic-embed-text")
KNOWLEDGE_DIR = "knowledge_base"
DB_DIR = "chroma_db_local"

# Configura Embeddings
#embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
embeddings = OllamaEmbeddings(model="nomic-embed-text")

def carregar_documentos(pasta_brain):
    """Lê todos os PDFs e TXTs de uma pasta específica"""
    documentos = []
    path = os.path.join(KNOWLEDGE_DIR, pasta_brain)
    
    if not os.path.exists(path):
        print(f"⚠️ Pasta não encontrada: {path}. Criando...")
        os.makedirs(path)
        return []

    for arquivo in os.listdir(path):
        file_path = os.path.join(path, arquivo)
        try:
            if arquivo.endswith(".pdf"):
                # MUDANÇA AQUI: PyMuPDF é muito mais forte que PyPDF
                loader = PyMuPDFLoader(file_path) 
                documentos.extend(loader.load())
                print(f"  📄 Carregado: {arquivo}")
            elif arquivo.endswith(".txt") or arquivo.endswith(".md"):
                loader = TextLoader(file_path, encoding='utf-8')
                documentos.extend(loader.load())
                print(f"  📄 Carregado: {arquivo}")
        except Exception as e:
            print(f"  ❌ Erro ao ler {arquivo}: {e}")
            
    return documentos

def treinar_cerebro(brain_id):
    print(f"\n🧠 Treinando Cérebro: {brain_id.upper()}...")
    
    # 1. Carrega Arquivos
    docs = carregar_documentos(brain_id)
    if not docs:
        print("  Parece vazio. Adicione arquivos na pasta.")
        return

    # 2. Quebra em pedaços (Chunks)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    print(f"  ✂️ Conteúdo dividido em {len(splits)} fragmentos de memória.")

    # 3. Salva no Banco Vetorial (COM RATE LIMITING MANUAL)
    
    # Inicializa a conexão com o banco (sem adicionar dados ainda)
    vectorstore = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings,
        collection_name=brain_id
    )

    # Configuração do Lote
    batch_size = 5  # Processa apenas 5 pedaços por vez
    total_batches = (len(splits) + batch_size - 1) // batch_size

    print(f"  ⏳ Iniciando gravação em {total_batches} lotes (para respeitar a cota da API)...")

    for i in range(0, len(splits), batch_size):
        batch = splits[i : i + batch_size]
        try:
            vectorstore.add_documents(batch)
            print(f"    ✅ Lote {i//batch_size + 1}/{total_batches} salvo.")
            time.sleep(2) # PAUSA DE 2 SEGUNDOS ENTRE LOTES
        except Exception as e:
            print(f"    ❌ Erro no lote {i//batch_size + 1}: {e}")
            print("    ⏳ Aguardando 30s para tentar esfriar a API...")
            time.sleep(30) # Se der erro, espera mais tempo e tenta continuar o loop
            
    print(f"  🏁 Memória de {brain_id} atualizada!")

if __name__ == "__main__":
    # Limpa banco anterior (Opcional: Descomente se quiser resetar a memória sempre)
    # if os.path.exists(DB_DIR):
    #     shutil.rmtree(DB_DIR)
    #     print("🧹 Memória antiga limpa.")

    # Treina os 3 cérebros
    treinar_cerebro("ds_analytics")
    treinar_cerebro("iqm_diretoria")
    treinar_cerebro("brasfort_global")
    
    print("\n🚀 Treinamento Concluído!")