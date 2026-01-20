from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from database import DataManager
import datetime
import os
import automation
import organizer
import model_manager
import personas
import threading

# --- IMPORTS HÍBRIDOS ---
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.callbacks import BaseCallbackHandler
from dotenv import load_dotenv

# --- IMPORT DA VOZ ---
from vocal_core import VocalCore

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
user_session = {"active_brain": "strategist", "chat_history": []}

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

# --- NOVA CLASSE DE STREAMING (VISUAL + ÁUDIO) ---
class VoiceSocketCallback(BaseCallbackHandler):
    def __init__(self, brain_name):
        self.brain_name = brain_name
        self.text_buffer = ""
        
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        # 1. Envia pro Frontend (Visual)
        socketio.emit('ai_stream', {'chunk': token})
        
        # 2. Acumula para a Voz (Bufferização Inteligente)
        if vocal:
            self.text_buffer += token
            # Se encontrar pontuação, manda o trecho para o Kokoro falar
            if any(p in token for p in ['.', '!', '?', ':', '\n']):
                voice_id = vocal.get_voice_for_brain(self.brain_name)
                # Acessa o método interno para gerar fila
                vocal._generate_and_queue(self.text_buffer, voice_id)
                self.text_buffer = ""

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
    """Recebe o Like/Dislike do Frontend"""
    data = request.json
    brain = data.get('brain')
    score = data.get('score')
    
    print(f"\n⭐ FEEDBACK RECEBIDO! Cérebro: {brain} | Nota: {score}")
    print(f"   (Gravado no Banco de Dados)\n")

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
    
    emit('vision_feedback', {'type': tipo, 'msg': msg})
    
    if tipo == 'GESTURE_LOCK':
        try:
            automation.bloquear_windows()
        except:
            pass
    elif tipo == 'GESTURE_REPORT':
        emit('status_update', {'msg': '✌️ Gesto "V" detectado: Iniciando Relatórios...'})

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
    texto_lower = user_text.lower()
    
    # 1. Definição de Cérebro (Com persistência)
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

    try:
        emit('ai_stream_start', {})
        
        # 2. Interrompe voz anterior
        if vocal:
            vocal.stop()
        
        # 3. Automação Rápida
        system_log = ""
        if "bloquear" in texto_lower:
            automation.bloquear_windows()
            system_log = "[AÇÃO: Windows Bloqueado]"
        
        # 4. Prompt
        prompt_final = f"""
        PERSONA: {brain_data['instruction']}
        LOG DE SISTEMA: {system_log}
        USUÁRIO: {user_text}
        """

        # 5. Geração com Callback de Voz
        voice_callback = VoiceSocketCallback(brain_data["name"])
        generate_function = model_manager.get_fallback_model(callbacks=[voice_callback])
        
        response_obj = generate_function(prompt_final)
        final_text = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
        
        emit('ai_stream_end', {'full_text': final_text})
        
    except Exception as e:
        print(f"Erro: {e}")
        emit('ai_response', {'text': f"Erro: {str(e)}"})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)