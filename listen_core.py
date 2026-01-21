import speech_recognition as sr
from faster_whisper import WhisperModel
import socketio
import os
import time
import io
import numpy as np

# ==========================================
# 👂 CONFIGURAÇÃO DO LISTEN CORE (V2 - ESTABILIZADO)
# ==========================================
ARGUS_URL = 'http://localhost:5000'
MODEL_SIZE = "base"
COMPUTE_TYPE = "int8"

print(f"⏳ Carregando Modelo Whisper ({MODEL_SIZE})...")
try:
    audio_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)
    print("✅ Modelo Whisper Carregado!")
except Exception as e:
    print(f"❌ Erro ao carregar Whisper: {e}")
    exit()

sio = socketio.Client()

try:
    sio.connect(ARGUS_URL)
    print("🔗 Conectado ao Servidor Argus!")
except:
    print("⚠️ Servidor Argus offline. Modo Debug.")

# ==========================================
# 🎤 LOOP DE ESCUTA
# ==========================================
def run_listener():
    recognizer = sr.Recognizer()
    
    # --- AJUSTE FINO DE SENSIBILIDADE ---
    # Se estiver captando muito ruído, AUMENTE este valor (Ex: 3000, 4000)
    # Se não estiver te ouvindo, DIMINUA (Ex: 1000, 500)
    recognizer.energy_threshold = 2000  
    
    # Desliguei o dinâmico pq ele costuma baixar demais a régua no silêncio
    recognizer.dynamic_energy_threshold = False 
    
    # Tempo de silêncio para considerar que a frase acabou (era 0.8)
    recognizer.pause_threshold = 1.0  
    
    # Ignora frases muito curtas (barulhos de tosse, batidas)
    recognizer.non_speaking_duration = 0.4

    with sr.Microphone() as source:
        print(f"\n🎧 Configurado! Limiar de Ruído: {recognizer.energy_threshold}")
        print("🟢 ARGUS OUVINDO... (Fale com clareza)")

        while True:
            try:
                # phrase_time_limit=10 evita que ele grave o ar condicionado infinitamente
                audio_data = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                
                # print("⏳ Processando áudio...") # Comentei pra limpar o log
                
                # Converte para Whisper
                wav_data = audio_data.get_wav_data()
                audio_stream = io.BytesIO(wav_data)

                # Transcreve
                segments, info = audio_model.transcribe(
                    audio_stream, 
                    beam_size=5, 
                    language="pt",
                    vad_filter=True, # Filtro de voz nativo do Whisper (Ajuda muito!)
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                
                final_text = ""
                for segment in segments:
                    final_text += segment.text
                
                final_text = final_text.strip()
                
                # --- FILTRO DE ALUCINAÇÕES ---
                # O Whisper adora inventar essas frases no silêncio
                alucinacoes = ["Obrigado.", "Legendas por...", "Amara.org", "Sous-titres", "Hmm"]
                
                eh_alucinacao = any(x in final_text for x in alucinacoes)
                
                if final_text and len(final_text) > 3 and not eh_alucinacao:
                    print(f"🗣️ VOCÊ DISSE: {final_text}")
                    
                    # Comandos Locais
                    if "parar audição" in final_text.lower():
                        print("🛑 Parando a escuta.")
                        break

                    # Envia
                    try:
                        sio.emit('user_message', {'message': final_text})
                    except:
                        pass
                else:
                    # Se caiu aqui, era ruído ou alucinação
                    pass 

            except KeyboardInterrupt:
                break
            except Exception as e:
                # print(f"⚠️ Erro leve: {e}") 
                pass

if __name__ == "__main__":
    run_listener()