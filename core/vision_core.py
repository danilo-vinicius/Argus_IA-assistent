import cv2
import mediapipe as mp
import socketio
import time
import base64

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

# Variáveis de Controle
gesture_state = {
    "LOCK":   {"start_time": 0, "triggered": False, "duration": 1.5, "color": (0, 0, 255)}, 
    "SCREEN": {"start_time": 0, "triggered": False, "duration": 1.0, "color": (0, 255, 0)}
}
current_stable_gesture = None
consecutive_frames = 0
FRAMES_TO_STABILIZE = 8 
last_execution_time = 0
COOLDOWN_GLOBAL = 3.0

def is_finger_folded(lm, tip_idx, joint_idx):
    return lm[tip_idx].y > lm[joint_idx].y

def get_gesture(hand_landmarks):
    lm = hand_landmarks.landmark
    fingers_folded = 0
    if is_finger_folded(lm, 8, 6): fingers_folded += 1 
    if is_finger_folded(lm, 12, 10): fingers_folded += 1
    if is_finger_folded(lm, 16, 14): fingers_folded += 1
    if is_finger_folded(lm, 20, 18): fingers_folded += 1
    
    thumb_tip_y = lm[4].y
    thumb_base_y = lm[2].y
    thumb_is_up = thumb_tip_y < thumb_base_y 

    if thumb_is_up and fingers_folded >= 3: return "SCREEN"
    if not thumb_is_up and fingers_folded == 4: return "LOCK"
    return None

def process_logic(frame, raw_gesture_name):
    global current_stable_gesture, consecutive_frames, last_execution_time

    if raw_gesture_name == current_stable_gesture:
        consecutive_frames += 1
    else:
        consecutive_frames = 0
        current_stable_gesture = raw_gesture_name
        for g in gesture_state.values(): g["start_time"] = 0

    if consecutive_frames < FRAMES_TO_STABILIZE: return
    if current_stable_gesture is None: return

    if time.time() - last_execution_time < COOLDOWN_GLOBAL:
        cv2.putText(frame, "Cooling down...", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2)
        return

    state = gesture_state[current_stable_gesture]
    
    if state["start_time"] == 0:
        state["start_time"] = time.time()
        state["triggered"] = False
    else:
        elapsed = time.time() - state["start_time"]
        remaining = state["duration"] - elapsed
        
        text = f"{current_stable_gesture}: {remaining:.1f}s"
        cv2.putText(frame, text, (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, state["color"], 2)
        
        if elapsed >= state["duration"] and not state["triggered"]:
            state["triggered"] = True
            last_execution_time = time.time()
            state["start_time"] = 0 
            
            if current_stable_gesture == "LOCK":
                try: sio.emit('vision_event', {'type': 'GESTURE_LOCK', 'message': 'Bloqueando...'})
                except: pass
            elif current_stable_gesture == "SCREEN":
                try: sio.emit('vision_event', {'type': 'GESTURE_SCREEN', 'message': '📸 Print...'})
                except: pass

def run_vision():
    cap = cv2.VideoCapture(0)
    # Reduz resolução para não travar o socket (320x240 é leve e suficiente para preview)
    cap.set(3, 480)
    cap.set(4, 360)

    with mp_pose.Pose(min_detection_confidence=0.5) as pose, \
         mp_hands.Hands(min_detection_confidence=0.8, max_num_hands=1) as hands:
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            results_hands = hands.process(image)
            detected_gesture = None

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) # Volta para BGR para desenhar

            if results_hands.multi_hand_landmarks:
                for hand_landmarks in results_hands.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    detected_gesture = get_gesture(hand_landmarks)
            
            process_logic(image, detected_gesture)

            # --- STREAMING PARA O FRONTEND ---
            # 1. Codifica para JPG
            _, buffer = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            # 2. Converte para Base64
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            # 3. Envia
            try:
                sio.emit('video_stream', {'image': jpg_as_text})
            except:
                pass

            # Janela Local (Opcional - Pode comentar se quiser só no site)
            #cv2.imshow('Argus Vision Core', image)
            #if cv2.waitKey(5) & 0xFF == ord('q'):
                #break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_vision()