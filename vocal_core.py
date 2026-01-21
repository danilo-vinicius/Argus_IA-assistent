import os
import sys
import threading
import queue
import time
import sounddevice as sd
import numpy as np
import re  # Import necessário para limpar o texto (Regex)

# ==============================================================================
# 🔧 CONFIGURAÇÃO PORTÁTIL (V2 - BLINDADA)
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DLL_PATH = os.path.join(BASE_DIR, "libespeak-ng.dll")
DATA_PATH = os.path.join(BASE_DIR, "espeak-ng-data")

print(f"🔍 [DIAGNOSTICO] Verificando estrutura de arquivos:")
print(f"   📂 Raiz: {BASE_DIR}")
print(f"   📄 DLL Alvo: {DLL_PATH} -> {'✅ Existe' if os.path.exists(DLL_PATH) else '❌ NÃO ACHEI'}")
print(f"   📂 DATA Alvo: {DATA_PATH} -> {'✅ Existe' if os.path.exists(DATA_PATH) else '❌ NÃO ACHEI'}")

if os.path.exists(DLL_PATH) and os.path.exists(DATA_PATH):
    print(f"✅ [CONFIG] Ativando Modo Portátil!")
    os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = DLL_PATH
    os.environ["ESPEAK_DATA_PATH"] = DATA_PATH
    os.environ["PATH"] = BASE_DIR + ";" + os.environ["PATH"]
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(BASE_DIR)
        except:
            pass
else:
    print("❌ [ERRO CRÍTICO] Falta arquivo DLL ou pasta espeak-ng-data na raiz!")

# ==============================================================================

from kokoro import KPipeline

LANG_CODE = 'p' 
VOICE_SPEED = 0.9  # Ajustado conforme sua preferência (0.9 é mais natural)

VOICE_MAP = {
    "The Architect": "pm_alex",
    "The Strategist": "pm_alex",
    "The Operator": "pm_alex",
    "The Polymath": "pf_dora"
}

class VocalCore:
    def __init__(self):
        print("🎙️ [INIT] Inicializando Kokoro TTS...")
        try:
            self.pipeline = KPipeline(lang_code=LANG_CODE)
            self.audio_queue = queue.Queue()
            self.stop_event = threading.Event()
            
            t = threading.Thread(target=self._playback_worker, daemon=True)
            t.start()
            print("✅ [INIT] Vocal Core Online.")
        except Exception as e:
            print(f"❌ [INIT ERROR] Falha no Kokoro: {e}")
            self.pipeline = None

    def _playback_worker(self):
        print("🧵 [THREAD] Worker de áudio pronto.")
        while True:
            try:
                item = self.audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            if item is None: break
            
            audio_chunk, sample_rate = item
            
            try:
                if not self.stop_event.is_set():
                    sd.play(audio_chunk, sample_rate)
                    sd.wait()
            except Exception as e:
                print(f"❌ [PLAYBACK ERROR] {e}")
            finally:
                self.audio_queue.task_done()

    def speak_stream(self, text_stream, brain_name="The Architect"):
        pass 

    def _clean_text(self, text):
        """Remove caracteres Markdown que sujam a fala (*, #, _, etc)"""
        # Remove asteriscos duplos ou simples (Negrito/Itálico)
        text = text.replace('**', '').replace('*', '')
        # Remove hashtags de títulos (# Titulo)
        text = text.replace('#', '')
        # Remove crases de código
        text = text.replace('`', '')
        # Remove underlines
        text = text.replace('_', ' ')
        return text

    def _generate_and_queue(self, text, voice):
        if not self.pipeline: return
        
        self.stop_event.clear()
        
        # 1. Limpa o texto antes de processar
        clean_text = self._clean_text(text)
        
        # print(f"⚙️ [KOKORO] Processando: '{clean_text[:20]}...'")
        
        try:
            if self.stop_event.is_set(): return

            # Usa a velocidade definida (0.9)
            generator = self.pipeline(clean_text, voice=voice, speed=VOICE_SPEED, split_pattern=None)
            
            # --- STREAMING INTELIGENTE ---
            audio_buffer = []
            buffer_length = 0
            MIN_PLAY_SIZE = 12000 
            
            if generator:
                for result in generator:
                    if self.stop_event.is_set(): break
                    
                    if len(result) == 3:
                        _, _, audio = result
                        if audio is not None and len(audio) > 0:
                            audio_buffer.append(audio)
                            buffer_length += len(audio)
                            
                            if buffer_length >= MIN_PLAY_SIZE:
                                chunk_completo = np.concatenate(audio_buffer)
                                self.audio_queue.put((chunk_completo, 24000))
                                audio_buffer = []
                                buffer_length = 0
            
            if audio_buffer:
                chunk_final = np.concatenate(audio_buffer)
                self.audio_queue.put((chunk_final, 24000))

        except Exception as e:
            print(f"❌ [ERRO] {e}")

    def get_voice_for_brain(self, brain_name):
        for key, voice in VOICE_MAP.items():
            if key in brain_name:
                return voice
        return "pm_alex"

    def stop(self):
        self.stop_event.set()
        sd.stop()
        if hasattr(self, 'audio_queue'):
            with self.audio_queue.mutex:
                self.audio_queue.queue.clear()