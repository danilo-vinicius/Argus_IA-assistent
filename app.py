from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler

import datetime
import os
import threading
import psutil
import pyautogui
import base64
from io import BytesIO

# --- abrir programas python ---
import subprocess
import sys

# --- IMPORTS HÍBRIDOS ---
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.callbacks import BaseCallbackHandler
from dotenv import load_dotenv

# --- IMPORT DA PACOTES ---
from skills import automation, organizer
from brain import model_manager, personas, memory_core
from core.vocal_core import VocalCore
from data.database import DataManager

# --- IMPORT NOTION ---
from skills.notion_manager import NotionManager

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "argus_secret")
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=600, ping_interval=25)
db = DataManager()

# --- INICIALIZAÇÃO DA VOZ ---
print("⏳ Carregando Módulo de Voz...")
try:
    vocal = VocalCore()
except Exception as e:
    print(f"⚠️ Erro ao iniciar voz: {e}")
    vocal = None

# --- MEMÓRIA & CONFIGURAÇÕES ---
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=ollama_host)
DB_DIR = "chroma_db_local"
user_session = {"active_brain": "strategist", "chat_history": [], "focus_task": None}

# --- SCHEDULER (AUTONOMIA) ---
scheduler = BackgroundScheduler()

def rotina_de_curiosidade():
    """Roda a cada 1 hora: Verifica lacunas de conhecimento e 'estuda'"""
    print("🔎 [ARGUS AUTONOMOUS] Verificando lacunas de conhecimento...")
    try:
        pendencias = db.get_curiosidades_pendentes()
        if pendencias:
            print(f"   Encontrei {len(pendencias)} temas para estudar.")
        else:
            print("   Nenhuma lacuna crítica encontrada.")
    except:
        pass

if not scheduler.running:
    scheduler.add_job(func=rotina_de_curiosidade, trigger="interval", minutes=60)
    scheduler.start()


# --- CONTROLE DE PROCESSOS (VISION) ---
vision_process = None
voice_active = True    # Começa falando
mic_active = True      # Começa ouvindo
notion_brain = NotionManager() # O Argus já nasce conectado


# --- CLASSE DE STREAMING (VISUAL + ÁUDIO) ---
class VoiceSocketCallback(BaseCallbackHandler):
    def __init__(self, brain_name):
        self.brain_name = brain_name
        self.text_buffer = ""
        # Debug: Avisa que iniciou
        print(f"🎤 [VOICE DEBUG] Callback iniciado para o cérebro: {brain_name}")
        
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        socketio.emit('ai_stream', {'chunk': token})
        
        # --- SÓ FALA SE O BOTÃO ESTIVER LIGADO ---
        global voice_active
        if vocal and voice_active:
            self.text_buffer += token
            
            # Só fala se encontrar pontuação FINAL (. ? !) ou quebra de linha
            if any(p in token for p in ['.', '?', '!', '\n']):
                texto_limpo = self.text_buffer.strip()
                # --- FILTRO ANTI-GARGALO ---
                if len(texto_limpo) > 15 or '\n' in token:
                    voice_id = vocal.get_voice_for_brain(self.brain_name)
                    try:
                        vocal._generate_and_queue(self.text_buffer, voice_id)
                    except Exception as e:
                        print(f"❌ [ERRO VOZ] {e}")
                    self.text_buffer = "" # Limpa o buffer
        else:
            pass

# --- CLASSE DE STREAMING SILENCIOSA (SÓ TEXTO) ---
# Usada para textos longos (Planos, Códigos) para não travar a geração
class SilentSocketCallback(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        # Só manda pro site, não chama o vocal_core
        socketio.emit('ai_stream', {'chunk': token})


# --- SENTIDOS DO ARGUS ---
@socketio.on('toggle_vision')
def handle_vision_toggle(data):
    global vision_process
    action = data.get('action')
    
    script_path = os.path.join("core", "vision_core.py")
    
    if action == 'start':
        if vision_process is None:
            print("👁️ [SISTEMA] Iniciando Módulo de Visão...")
            try:
                vision_process = subprocess.Popen([sys.executable, script_path])
                emit('vision_status', {'status': 'online'}, broadcast=True)
            except Exception as e:
                print(f"❌ Erro ao iniciar visão: {e}")
        else:
            print("⚠️ Visão já está rodando.")

    elif action == 'stop':
        if vision_process:
            print("👁️ [SISTEMA] Desligando Módulo de Visão...")
            vision_process.terminate()
            vision_process = None
            emit('vision_status', {'status': 'offline'}, broadcast=True)
        else:
            print("⚠️ Visão já está desligada.")

@socketio.on('toggle_ears')
def handle_ears_toggle(data):
    global mic_active
    action = data.get('action')
    
    if action == 'start':
        mic_active = True
        print("👂 [SISTEMA] Microfone DESMUTADO.")
        emit('ears_status', {'status': 'online'}, broadcast=True)
    else:
        mic_active = False
        print("🔕 [SISTEMA] Microfone MUTADO.")
        emit('ears_status', {'status': 'offline'}, broadcast=True)

# --- COMANDO DE INTELIGÊNCIA: NOTION ---
@socketio.on('check_tasks')
def handle_check_tasks(data):
    print("🧠 [ARGUS] Consultando Banco de Dados Corporativo...")
    
    tarefas = notion_brain.get_pending_tasks()
    
    if not tarefas:
        msg = "Sr. Danilo, consultei o banco oficial e não encontrei nenhuma pendência com status 'Não iniciado'. Estamos livres!"
        emit('ai_stream_start', {})
        emit('ai_stream', {'chunk': msg})
        emit('ai_stream_end', {})
        
        if voice_active and vocal: vocal.generate_audio(msg)
        return

    # --- LÓGICA DE FOCO (MEMÓRIA) ---
    altas = [t for t in tarefas if t['priority'] == 'Alta']
    top_task = altas[0] if altas else tarefas[0]
    
    # SALVA NA SESSÃO
    user_session["focus_task"] = top_task
    print(f"🎯 [FOCO] Tarefa Prioritária definida: {top_task['title']}")
    # -------------------------------

    # Relatório Visual
    relatorio = "📋 **RELATÓRIO DE PENDÊNCIAS BRASFORT**:\n\n"
    for t in tarefas:
        icon = "🔴" if t['priority'] == "Alta" else "🟡" if t['priority'] == "Média" else "🔵"
        relatorio += f"{icon} **{t['title']}** (Prioridade: {t['priority']})\n"
    
    relatorio += f"\n\n🤔 *A tarefa mais crítica é **{top_task['title']}**. Diga 'Gerar Plano' para criar a estratégia no Playground.*"

    emit('ai_stream_start', {})
    emit('ai_stream', {'chunk': relatorio})
    emit('ai_stream_end', {})

    if voice_active and vocal:
        resumo_voz = f"Encontrei {len(tarefas)} pendências. A prioridade é: {top_task['title']}."
        vocal.generate_audio(resumo_voz, brain="strategist")

@socketio.on('toggle_voice')
def handle_voice_toggle(data):
    global voice_active
    action = data.get('action')
    
    if action == 'start':
        voice_active = True
        print("🗣️ [SISTEMA] Voz ATIVADA.")
        emit('voice_status', {'status': 'online'}, broadcast=True)
    else:
        voice_active = False
        if vocal: vocal.stop()
        print("🤫 [SISTEMA] Voz MUTADA.")
        emit('voice_status', {'status': 'offline'}, broadcast=True)

# --- ROTAS FLASK ---
@app.route('/')
def home():
    brain = personas.get_active_brain()
    if isinstance(user_session.get("active_brain"), dict):
        brain = user_session["active_brain"]
    else:
        user_session["active_brain"] = brain
        
    return render_template('index.html', 
                          brain_name=brain["name"], 
                          brain_color=brain["color"])

@app.route('/api/reward', methods=['POST'])
def registrar_recompensa():
    data = request.json
    brain = data.get('brain')
    score = data.get('score')
    
    print(f"\n⭐ FEEDBACK RECEBIDO! Cérebro: {brain} | Nota: {score}")
    
    db.registrar_recompensa(
        brain_id=brain,
        query=data.get('query'),
        response=data.get('response'),
        score=score
    )
    return jsonify({"status": "feedback_registrado"})

# --- SOCKET EVENTS ---
@socketio.on('connect')
def handle_connect():
    brain = user_session.get("active_brain")
    if not isinstance(brain, dict):
        brain = personas.get_active_brain()
        user_session["active_brain"] = brain
        
    emit('status_update', {'msg': f'Conectado. Cérebro: {brain["name"]}', 'color': brain["color"]})

@socketio.on('vision_event')
def handle_vision(data):
    tipo = data.get('type')
    msg = data.get('message')
    print(f"👁️ VISÃO COMPUTACIONAL: {tipo} - {msg}")
    
    emit('status_update', {'msg': f'👁️ {msg}'})
    
    if tipo == 'GESTURE_LOCK':
        automation.bloquear_windows()
        
    elif tipo == 'GESTURE_SCREEN':
        print("📸 Iniciando captura de tela via Gesto...")
        analisar_tela_agora()

@socketio.on('video_stream')
def handle_video_stream(data):
    emit('video_stream', data, broadcast=True)

def analisar_tela_agora():
    """Função auxiliar para tirar print e mandar pro Gemini"""
    try:
        screenshot = pyautogui.screenshot()
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        brain = user_session.get("active_brain", personas.BRAINS["architect"])
        prompt_text = f"""
        PERSONA: {brain['instruction']}
        TAREFA: O usuário mandou um print da tela dele. Analise o código, o erro ou o gráfico.
        Seja direto.
        """
        
        print("🚀 Enviando imagem para o Gemini...")
        emit('ai_stream_start', {})
        
        voice_callback = VoiceSocketCallback(brain["name"])
        generate_function = model_manager.get_fallback_model(callbacks=[voice_callback])
        
        response = generate_function(prompt_text, image_data=img_str)
        final_text = response.content
        emit('ai_stream_end', {'full_text': final_text})
        
    except Exception as e:
        print(f"❌ Erro ao analisar tela: {e}")
        emit('ai_response', {'text': "Não consegui ver sua tela, chefe."})

@socketio.on('manual_brain_switch')
def handle_manual_switch(data):
    key = data.get('brain_key')
    if key in personas.BRAINS:
        brain_data = personas.BRAINS[key]
        user_session["active_brain"] = brain_data
        
        emit('brain_change', {'name': brain_data["name"], 'color': brain_data["color"]})
        emit('status_update', {'msg': f'🔄 Modulação Manual: {brain_data["name"]} Ativado.'})
        print(f"🎛️ Troca Manual para: {brain_data['name']}")

@socketio.on('user_message')
def handle_message(data):
    user_text = data.get('message')
    source = data.get('source', 'text')
    
    # --- 1. TRAVA DE SEGURANÇA PARA COMANDOS ---
    if user_text.strip().startswith('/'):
        print(f"🛑 [ARGUS] Comando '{user_text}' interceptado. LLM ignorado.")
        return 
    
    # --- 2. CONTROLE DE MUTE DO MICROFONE ---
    if source == 'audio' and not mic_active:
        return

    # --- 3. ESPELHO DE ÁUDIO NO CHAT ---
    if source == 'audio':
        emit('mirror_user_message', {'message': user_text})
    
    texto_lower = user_text.lower()

    # ============================================================
    # 🚀 4. INTEGRAÇÃO NOTION: GERADOR DE PLANO DE AÇÃO
    # ============================================================
    if "plano" in texto_lower and ("ação" in texto_lower or "gerar" in texto_lower):
        
        task = user_session.get("focus_task")
        
        if not task:
            emit('ai_stream_start', {})
            emit('ai_stream', {'chunk': "⚠️ Não tenho nenhuma tarefa prioritária na memória. Por favor, use o comando **/notion** primeiro."})
            emit('ai_stream_end', {})
            if voice_active and vocal: vocal.generate_audio("Não sei de qual tarefa você está falando. Rode o comando notion primeiro.")
            return

        print(f"🏗️ [ARGUS] Analisando demanda: {task['title']}...")

        # --- TRAVA DE DUPLICIDADE ---
        if notion_brain.check_existing_plan(task['title']):
            msg = f"⚠️ Já encontrei um plano estratégico salvo para **'{task['title']}'** no seu Notion.\n\nNão vou gerar duplicado para economizar recursos."
            emit('ai_stream_start', {})
            emit('ai_stream', {'chunk': msg})
            emit('ai_stream_end', {})
            if voice_active and vocal: vocal.generate_audio("Senhor, já existe um plano para essa tarefa no seu arquivo. Operação cancelada.")
            return
        # ---------------------------

        emit('ai_stream_start', {})
        emit('ai_stream', {'chunk': f"⚙️ **Iniciando Protocolo The Strategist...**\n\nCriando plano tático para: *{task['title']}*...\n\n"})
        
        prompt_plano = f"""
        ATUE COMO: The Strategist.
        TAREFA: Crie um Plano de Ação Técnico detalhado para a seguinte demanda.
        DEMANDA: {task['title']}
        CONTEXTO: O usuário é Data Scientist e Analista de TI na Brasfort.
        FORMATO: Markdown (Checklists e Etapas).
        """
        
        try:
            # --- MODO SILENCIOSO ATIVADO PARA VELOCIDADE ---
            print("🤫 [ARGUS] Gerando em Modo Silencioso (Texto Longo)...")
            silent_callback = SilentSocketCallback() 
            
            # Passa o callback silencioso pro modelo (SEM VOZ)
            generate_function = model_manager.get_fallback_model(callbacks=[silent_callback])
            response = generate_function(prompt_plano)
            conteudo_plano = response.content
            
            # Posta no Notion
            emit('ai_stream', {'chunk': "\n\n💾 *Salvando no Notion Playground...*"})
            url = notion_brain.create_insight(title=f"Plano: {task['title']}", content=conteudo_plano)
            
            if url:
                final_msg = f"\n\n✅ **Plano Criado com Sucesso!**\nAcesse aqui: [Ver no Notion]({url})"
                emit('ai_stream', {'chunk': final_msg})
                if voice_active and vocal: vocal.generate_audio("Plano criado e salvo no seu Notion pessoal.")
            else:
                emit('ai_stream', {'chunk': "\n\n❌ Erro ao salvar no Notion."})
        
        except Exception as e:
            print(f"Erro ao gerar plano: {e}")
            emit('ai_stream', {'chunk': f"Erro: {str(e)}"})
            
        emit('ai_stream_end', {})
        return # Encerra aqui, não passa pro chat normal
    # ============================================================

    # --- 5. SELEÇÃO DE CÉREBRO ---
    if "código" in texto_lower or "python" in texto_lower:
        brain_data = personas.BRAINS["architect"]
    elif "relatório" in texto_lower or "kpi" in texto_lower:
        brain_data = personas.BRAINS["strategist"]
    elif "automação" in texto_lower or "abrir" in texto_lower:
        brain_data = personas.BRAINS["operator"]
    elif "inglês" in texto_lower or "postura" in texto_lower:
        brain_data = personas.BRAINS["polymath"]
    else:
        current = user_session.get("active_brain")
        if isinstance(current, dict):
            brain_data = current
        else:
            brain_data = personas.get_active_brain()

    user_session["active_brain"] = brain_data
    emit('brain_change', {'name': brain_data["name"], 'color': brain_data["color"]})

    # --- 6. GERAÇÃO DE RESPOSTA (LLM + RAG) ---
    try:
        emit('ai_stream_start', {})
        
        if vocal: vocal.stop()
        
        # Automação rápida
        system_log = ""
        if "bloquear" in texto_lower:
            automation.bloquear_windows()
            system_log = "[AÇÃO: Windows Bloqueado]"
        
        # RAG
        contexto_memoria = ""
        try:
            docs = memory_core.buscar_memoria(user_text)
            if docs:
                contexto_memoria = "\nCONHECIMENTO RECUPERADO:\n"
                for i, doc in enumerate(docs):
                    contexto_memoria += f"-- {doc.page_content}\n"
                print(f"🧠 [RAG] Encontrei {len(docs)} referências.")
        except Exception as e:
            print(f"⚠️ Erro no RAG: {e}")

        # Prompt Final
        prompt_final = f"""
        PERSONA: {brain_data['instruction']}
        {contexto_memoria}
        LOG DE SISTEMA: {system_log}
        USUÁRIO: {user_text}
        """

        voice_callback = VoiceSocketCallback(brain_data["name"])
        generate_function = model_manager.get_fallback_model(callbacks=[voice_callback])
        
        response_obj = generate_function(prompt_final)
        final_text = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
        
        emit('ai_stream_end', {'full_text': final_text})
        
    except Exception as e:
        print(f"Erro: {e}")
        emit('ai_stream', {'chunk': f"Erro fatal no núcleo: {str(e)}"})
        emit('ai_stream_end', {})

# --- THREAD DE MONITORAMENTO DE SISTEMA ---
def monitor_system():
    while True:
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            ram_usage = psutil.virtual_memory().percent
            socketio.emit('system_stats', {'cpu': cpu_usage, 'ram': ram_usage})
        except:
            pass

threading.Thread(target=monitor_system, daemon=True).start()

if __name__ == '__main__':
    print("🚀 INICIANDO SERVIDOR ARGUS...")

    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        startupinfo = None

    print("👂 Iniciando Serviço de Audição em Background...")
    ears_process = subprocess.Popen(
        [sys.executable, "core/listen_core.py"],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )

    socketio.run(app, debug=False, port=5000, use_reloader=False, allow_unsafe_werkzeug=True)