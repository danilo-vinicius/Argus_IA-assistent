import cv2
import mediapipe as mp
import socketio
import time
import math

# Configuração do Cliente SocketIO
sio = socketio.Client()
ARGUS_URL = 'http://localhost:5000'

try:
    sio.connect(ARGUS_URL)
    print("👁️ Vision Core conectado ao Argus!")
except:
    print("⚠️ Aviso: Argus Offline. Vision Core rodando em modo isolado.")

# Configuração MediaPipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

# --- VARIÁVEIS DE CONTROLE ---
gesture_state = {
    "LOCK":   {"start_time": 0, "triggered": False, "duration": 1.5, "color": (0, 0, 255)}, 
    "SCREEN": {"start_time": 0, "triggered": False, "duration": 1.0, "color": (0, 255, 0)}
}

# Estabilização (Debounce)
current_stable_gesture = None
consecutive_frames = 0
FRAMES_TO_STABILIZE = 8  # Precisa manter o gesto por 8 frames antes de contar tempo
last_execution_time = 0
COOLDOWN_GLOBAL = 3.0

def is_finger_folded(lm, tip_idx, joint_idx):
    """Verifica se a ponta do dedo está abaixo da articulação média"""
    return lm[tip_idx].y > lm[joint_idx].y

def get_gesture(hand_landmarks):
    """
    Analisa a geometria e retorna APENAS o nome do gesto detectado naquele frame.
    Retorna None se não for nada claro.
    """
    lm = hand_landmarks.landmark
    
    # 1. Estado dos 4 dedos (Index a Pinky)
    fingers_folded = 0
    if is_finger_folded(lm, 8, 6): fingers_folded += 1   # Index
    if is_finger_folded(lm, 12, 10): fingers_folded += 1 # Middle
    if is_finger_folded(lm, 16, 14): fingers_folded += 1 # Ring
    if is_finger_folded(lm, 20, 18): fingers_folded += 1 # Pinky

    # 2. Estado do Dedão (Regra de Ouro)
    # Dedão "Pra cima" = Ponta (4) acima da articulação base (2)
    thumb_tip_y = lm[4].y
    thumb_base_y = lm[2].y
    thumb_is_up = thumb_tip_y < thumb_base_y 

    # --- CLASSIFICAÇÃO RÍGIDA ---
    
    # JOINHA: Dedão pra cima E pelo menos 3 dedos dobrados
    if thumb_is_up and fingers_folded >= 3:
        return "SCREEN"
    
    # BLOQUEIO: Dedão pra BAIXO/LADO (Não pode estar pra cima) E 4 dedos dobrados
    # Essa regra 'not thumb_is_up' é vital para não confundir com o joinha
    if not thumb_is_up and fingers_folded == 4:
        return "LOCK"
        
    return None

def process_logic(frame, raw_gesture_name):
    """Gerencia Estabilidade + Timer"""
    global current_stable_gesture, consecutive_frames, last_execution_time

    # 1. Lógica de Estabilização (Remove o 'pisca-pisca')
    if raw_gesture_name == current_stable_gesture:
        consecutive_frames += 1
    else:
        consecutive_frames = 0
        current_stable_gesture = raw_gesture_name
        # Reseta timers se mudou o gesto
        for g in gesture_state.values(): g["start_time"] = 0

    # Só processa se estiver estável (Firmou o gesto)
    if consecutive_frames < FRAMES_TO_STABILIZE:
        return

    # Se o gesto for None (mão aberta/repouso), não faz nada
    if current_stable_gesture is None:
        return

    # 2. Verifica Cooldown Global
    if time.time() - last_execution_time < COOLDOWN_GLOBAL:
        cv2.putText(frame, "Aguarde...", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2)
        return

    # 3. Processa o Timer do Gesto Estável
    state = gesture_state[current_stable_gesture]
    
    if state["start_time"] == 0:
        state["start_time"] = time.time()
        state["triggered"] = False
        print(f"⏳ Iniciando Timer: {current_stable_gesture}")
    else:
        elapsed = time.time() - state["start_time"]
        remaining = state["duration"] - elapsed
        
        # Desenha barra de progresso ou texto
        text = f"{current_stable_gesture}: {remaining:.1f}s"
        cv2.putText(frame, text, (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, state["color"], 2)
        
        # DISPARO
        if elapsed >= state["duration"] and not state["triggered"]:
            state["triggered"] = True
            last_execution_time = time.time()
            state["start_time"] = 0 # Reseta
            
            # Envia comando
            if current_stable_gesture == "LOCK":
                print("👊 COMANDO ENVIADO: BLOQUEIO")
                try: sio.emit('vision_event', {'type': 'GESTURE_LOCK', 'message': 'Bloqueando Windows...'})
                except: pass
            elif current_stable_gesture == "SCREEN":
                print("👍 COMANDO ENVIADO: TELA")
                try: sio.emit('vision_event', {'type': 'GESTURE_SCREEN', 'message': '📸 Analisando tela...'})
                except: pass

def run_vision():
    cap = cv2.VideoCapture(0)
    
    with mp_pose.Pose(min_detection_confidence=0.5) as pose, \
         mp_hands.Hands(min_detection_confidence=0.8, max_num_hands=1) as hands: # Apenas 1 mão para evitar conflito
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            results_hands = hands.process(image)
            
            detected_gesture = None

            if results_hands.multi_hand_landmarks:
                for hand_landmarks in results_hands.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # Pega o gesto "bruto" deste frame
                    detected_gesture = get_gesture(hand_landmarks)
            
            # Passa para o cérebro de estabilização
            process_logic(frame, detected_gesture)

            cv2.imshow('Argus Vision v5 (Stabilized)', frame)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_vision()