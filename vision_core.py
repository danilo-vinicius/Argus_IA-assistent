import cv2
import mediapipe as mp
import socketio
import time
import math
import ctypes

# Configuração do Cliente SocketIO (Para falar com o Argus)
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

# Variáveis de Controle
last_gesture_time = 0
GESTURE_COOLDOWN = 3.0 # Segundos entre gestos

def calculate_angle(a, b, c):
    """Calcula ângulo entre 3 pontos (para postura)"""
    # (Simplificado para este exemplo)
    return 0 

def detect_fist(hand_landmarks):
    # Lógica simples: Pontas dos dedos abaixo das articulações médias
    fingers_folded = 0
    # Verifica 4 dedos (Index a Pinky)
    for i in range(8, 21, 4): 
        if hand_landmarks.landmark[i].y > hand_landmarks.landmark[i-2].y:
            fingers_folded += 1
    return fingers_folded >= 4

def run_vision():
    global last_gesture_time
    cap = cv2.VideoCapture(0) # Webcam 0
    
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose, \
         mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5) as hands:
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            # Espelhar e converter cor
            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Processamento
            results_pose = pose.process(image)
            results_hands = hands.process(image)

            # --- LÓGICA DE POSTURA (POSE) ---
            if results_pose.pose_landmarks:
                # Pega coordenadas do Nariz, Ombro e Orelha
                landmarks = results_pose.pose_landmarks.landmark
                nose = landmarks[mp_pose.PoseLandmark.NOSE.value]
                shoulder_l = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                
                # Regra simples de Hiperlordose/Corcunda:
                # Se o nariz estiver muito abaixo ou muito à frente do ombro (dependendo do ângulo da câmera)
                # Aqui vamos usar uma regra dummy: Se o nariz baixar muito no eixo Y
                if nose.y > shoulder_l.y - 0.1: # Ajuste esse 0.1 na prática
                    # Envia alerta silencioso
                    if time.time() - last_gesture_time > 10: # Alerta a cada 10s
                        try: sio.emit('vision_event', {'type': 'POSTURE_BAD', 'message': '⚠️ Postura! Arrume a coluna.'})
                        except: pass
                        last_gesture_time = time.time()

            # --- LÓGICA DE GESTOS (MÃOS) ---
            if results_hands.multi_hand_landmarks:
                for hand_landmarks in results_hands.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # 1. Detectar Punho Fechado (Bloqueio)
                    if detect_fist(hand_landmarks):
                        if time.time() - last_gesture_time > GESTURE_COOLDOWN:
                            print("👊 Gesto: BLOQUEIO")
                            try: sio.emit('vision_event', {'type': 'GESTURE_LOCK', 'message': 'Bloqueando Windows...'})
                            except: pass
                            last_gesture_time = time.time()
                    
                    # 2. Detectar "V" de Vitória (Relatório) -> Implementar lógica de dedos abertos
            
            # Mostra a tela (Opcional, pode rodar invisível depois)
            cv2.imshow('Argus Vision (Pressione Q para sair)', frame)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_vision()