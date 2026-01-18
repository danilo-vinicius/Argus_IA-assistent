from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from database import DataManager
import datetime
import os
import automation
import organizer
import model_manager

# --- IMPORTS HÍBRIDOS (GOOGLE + OLLAMA) ---
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import BaseCallbackHandler
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=600, ping_interval=25)
db = DataManager()

# --- CONFIGURAÇÃO DA CHAVE DO GOOGLE ---
api_key_segura = os.getenv("GOOGLE_API_KEY")
if not api_key_segura:
    print("ERRO CRÍTICO: Chave de API não encontrada no arquivo .env")
os.environ["GOOGLE_API_KEY"] = api_key_segura

# --- CONFIGURAÇÃO DE MEMÓRIA (OLLAMA) ---
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url=ollama_host # <--- ADICIONAR ISSO
)
DB_DIR = "chroma_db_local"

# --- DEFINIÇÃO DOS CÉREBROS (PERSONAS) ---
BRAIN_INSTRUCTIONS = {
    "system_admin": """
        Você é o ARGUS (Núcleo Administrativo).
        Sua função é gerenciar o sistema, executar automações e organizar o ambiente digital do Danilo.
        Tom: Eficiente, minimalista e prestativo. Como um mordomo digital de alta tecnologia ou uma IA de nave (tipo JARVIS/FRIDAY).
        Não tente ensinar nada acadêmico, apenas confirme a execução de tarefas com precisão e brevidade.
    """,
    "ds_analytics": """
        Você é o ARGUS (Módulo Acadêmico).
        O Danilo está cursando pós-graduação em Ciência de Dados e Big Data Analytics.
        Use o contexto abaixo para ensinar. Ignore cabeçalhos de PDF. Foque no conteúdo técnico.
    """,
    "iqm_diretoria": """
        Você é o ARGUS (Módulo Corporativo).
        Sua função é vigiar os indicadores e qualidade da Empresa. "Empresa atual: Brasfort".
        Seja analítico, direto e executivo.
    """,
    "brasfort_global": """
        Você é o ARGUS (Módulo Operacional).
        Você possui a visão geral dos processos para o trabalho de analista e cientista de dados.
    """
}

user_session = {"active_brain": "ds_analytics", "chat_history": []}

# --- CLASSE DE STREAMING ---
class SocketIOCallback(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        socketio.emit('ai_stream', {'chunk': token})

def get_model_by_name(brain_key):
    """Retorna o modelo configurado para um cérebro específico"""
    
    # Se o cérebro não existir, usa o admin como fallback seguro
    system_prompt = BRAIN_INSTRUCTIONS.get(brain_key, BRAIN_INSTRUCTIONS["system_admin"])
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        streaming=True,
        callbacks=[SocketIOCallback()]
    )
    
    return llm, system_prompt

def query_knowledge(brain_id, query_text):
    """Busca Localmente usando Ollama Embeddings"""
    try:
        if not os.path.exists(DB_DIR): return None
        
        # O Admin não precisa buscar em PDF técnico, ele só executa.
        if brain_id == "system_admin": return None

        vectorstore = Chroma(
            persist_directory=DB_DIR, 
            embedding_function=embeddings, 
            collection_name=brain_id
        )
        
        results = vectorstore.similarity_search(query_text, k=3)
        if not results: return None
        return "\n\n".join([doc.page_content for doc in results])
    except Exception as e:
        print(f"Erro na busca local: {e}")
        return None

# --- ROTAS FLASK ---
@app.route('/')
def home():
    return render_template('index.html', saudacao="Argus Online (Híbrido)", foco="Cérebro: Gemini | Memória: Local", active_brain=user_session["active_brain"])

@app.route('/tasks')
def tasks_page():
    return render_template('tasks.html', tarefas_agrupadas={})

@app.route('/vault')
def vault_page():
    return render_template('vault.html', notas=[])

# --- SOCKET EVENTS ---
@socketio.on('connect')
def handle_connect():
    emit('status_update', {'msg': 'Sistema Híbrido Conectado.'})

@socketio.on('switch_brain')
def handle_brain_switch(data):
    user_session["active_brain"] = data.get('brain')
    emit('status_update', {'msg': f'Contexto: {user_session["active_brain"].upper()}'})

@socketio.on('user_message')
def handle_message(data):
    user_text = data.get('message')
    
    current_brain = user_session["active_brain"]
    brain_for_response = current_brain 
    
    try:
        emit('ai_stream_start', {})
        
        system_log = ""
        texto_lower = user_text.lower()

        # --- GATILHOS (MANTIDOS IGUAIS) ---
        gatilhos_matinais = ["rotina matinal", "começar o dia", "iniciar o dia", "modo trabalho", "vamos trabalhar"]
        gatilhos_limpeza = ["organizar arquivos", "organizar meus arquivos", "organizar os arquivos", "limpar downloads"]

        if any(gatilho in texto_lower for gatilho in gatilhos_matinais):
            emit('ai_stream', {'chunk': '⚡ Argus Synapse: Iniciando protocolos de trabalho...\n\n'})
            resultado_acao = automation.executar_rotina_matinal()
            system_log = f"[SISTEMA: {resultado_acao}]"
            brain_for_response = "system_admin"

        elif any(gatilho in texto_lower for gatilho in gatilhos_limpeza):
            emit('ai_stream', {'chunk': '🧹 Argus Local: Acessando sistema de arquivos...\n\n'})
            resultado_acao = organizer.organizar_downloads()
            system_log = f"[SISTEMA: {resultado_acao}]"
            brain_for_response = "system_admin"
        
        elif "abrir" in texto_lower and "outlook" in texto_lower:
            automation.abrir_app_windows("outlook")
            system_log = "[SISTEMA: Outlook aberto.]"
            brain_for_response = "system_admin"
        
        # --- PREPARAÇÃO DO PROMPT ---

        # 1. Busca Contexto (RAG)
        contexto_rag = query_knowledge(brain_for_response, user_text)
        
        # 2. Pega a Instrução do Sistema (Persona)
        # Se não achar o cérebro, usa o admin
        system_instruction = BRAIN_INSTRUCTIONS.get(brain_for_response, BRAIN_INSTRUCTIONS["system_admin"])
        
        prompt_final = f"""
        System: {system_instruction}
        
        Contexto Recuperado:
        {contexto_rag if contexto_rag else "Nenhum contexto específico necessário."}
        
        LOG DE AÇÕES DO SISTEMA:
        {system_log}
        
        Usuário: {user_text}
        
        Instrução: Se houver LOG DE AÇÕES, confirme a execução.
        """
        
        # --- GERAÇÃO INTELIGENTE (CASCATA) ---
        
        # Cria o callback de streaming
        callback_socket = SocketIOCallback()
        
        print(f"🤖 Solicitando resposta para: {brain_for_response}")
        
        if brain_for_response == "system_admin":
            # ECONOMIA: Se for Admin, usa direto o modelo LITE (sem cascata complexa, ou uma cascata só de lites)
            # Para simplificar, vamos usar a cascata normal, mas você poderia forçar o Lite aqui.
            generate_function = model_manager.get_fallback_model(callbacks=[callback_socket])
        else:
            # DATA SCIENCE/CORP: Usa a cascata completa (Melhor -> Pior)
            generate_function = model_manager.get_fallback_model(callbacks=[callback_socket])
        
        # Executa a geração (A mágica do Loop acontece aqui dentro)
        generate_function(prompt_final)
        
        emit('ai_stream_end', {})
        
    except Exception as e:
        print(f"Erro Crítico: {e}")
        emit('ai_response', {'text': f"⚠️ Falha nos sistemas neurais: {str(e)}"})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)