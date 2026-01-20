import threading
import queue
import time
import sounddevice as sd
import soundfile as sf
import numpy as np
from kokoro import KPipeline

# Configuração do Modelo
LANG_CODE = 'p' # 'p' => Brazilian Portuguese

# Mapeamento de Vozes por Cérebro
VOICE_MAP = {
    "The Architect": "pm_alex",   # Voz Masculina
    "The Strategist": "pm_alex",  # Voz Masculina
    "The Operator": "pm_alex",    # Voz Masculina
    "The Polymath": "pf_dora"     # Voz Feminina
}

class VocalCore:
    def __init__(self):
        print("🎙️ Inicializando Kokoro TTS (82M params)...")
        try:
            # Inicializa a Pipeline do Kokoro
            self.pipeline = KPipeline(lang_code=LANG_CODE)
            self.audio_queue = queue.Queue()
            self.is_speaking = False
            self.stop_event = threading.Event()
            
            # Inicia thread de reprodução
            threading.Thread(target=self._playback_worker, daemon=True).start()
            print("✅ Vocal Core Online (Kokoro-82M)")
        except Exception as e:
            print(f"❌ Erro ao carregar Vocal Core: {e}")
            print("DICA: Verifique se o eSpeak-ng está instalado e no PATH.")

    def _playback_worker(self):
        """Consome a fila de áudio e toca nos alto-falantes"""
        while True:
            item = self.audio_queue.get()
            if item is None: break # Sinal de parada
            
            audio_chunk, sample_rate = item
            self.is_speaking = True
            try:
                if not self.stop_event.is_set():
                    sd.play(audio_chunk, sample_rate)
                    sd.wait() # Espera terminar de falar
            except Exception as e:
                print(f"Erro de reprodução: {e}")
            finally:
                self.is_speaking = False
                self.audio_queue.task_done()

    def speak_stream(self, text_stream, brain_name="The Architect"):
        """
        Processa um gerador de texto (stream) e fala em tempo real.
        """
        self.stop_event.clear()
        voice_id = self.get_voice_for_brain(brain_name)
        
        buffer = ""
        split_chars = {'.', '!', '?', ':', '\n'} 
        
        print(f"🔈 Falando com voz: {voice_id}")

        for token in text_stream:
            if self.stop_event.is_set(): break
            
            buffer += token
            
            if any(char in token for char in split_chars) and len(buffer.strip()) > 5:
                self._generate_and_queue(buffer, voice_id)
                buffer = ""
        
        if buffer.strip():
            self._generate_and_queue(buffer, voice_id)

    def _generate_and_queue(self, text, voice):
        """Gera o áudio usando Kokoro e coloca na fila"""
        try:
            if self.stop_event.is_set(): return

            # O pipeline gera: (graphemes, phonemes, audio)
            # speed=1.1 deixa a fala um pouco mais fluida
            generator = self.pipeline(text, voice=voice, speed=1.1, split_pattern=None)
            
            for _, _, audio in generator:
                if self.stop_event.is_set(): break
                self.audio_queue.put((audio, 24000)) 
        except Exception as e:
            print(f"Erro na síntese: {e}")

    def get_voice_for_brain(self, brain_name):
        """Retorna o ID da voz baseado no nome do cérebro"""
        # Procura parcial (ex: "The Architect" -> "The Architect")
        for key, voice in VOICE_MAP.items():
            if key in brain_name:
                return voice
        return "pm_alex" # Padrão

    def stop(self):
        """Interrompe a fala imediatamente"""
        self.stop_event.set()
        sd.stop()
        # Limpa a fila
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()