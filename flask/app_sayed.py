import cv2
import mediapipe as mp
import pyautogui
import time
import os
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize MediaPipe Hands.
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# State variable to track the "liked" gesture
liked_state = False
liked_timestamp = time.time()

def recognize_gesture(landmarks, handedness):
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    thumb_mcp = landmarks[2]
    index_tip = landmarks[8]
    index_pip = landmarks[6]
    middle_tip = landmarks[12]
    middle_pip = landmarks[10]
    ring_tip = landmarks[16]
    ring_pip = landmarks[14]
    pinky_tip = landmarks[20]
    pinky_pip = landmarks[18]

    # Thumb up gesture: thumb is up and all other fingers are down
    thumb_up = thumb_tip.y < thumb_ip.y < thumb_mcp.y
    index_down = index_tip.y > index_pip.y
    middle_down = middle_tip.y > middle_pip.y
    ring_down = ring_tip.y > ring_pip.y
    pinky_down = pinky_tip.y > pinky_pip.y

    if thumb_up and index_down and middle_down and ring_down and pinky_down:
        return "liked"

    # Calculate the average y-coordinate of the MCP joints to determine if the hand is raised
    mcp_y_avg = (landmarks[5].y + landmarks[9].y + landmarks[13].y + landmarks[17].y) / 4

    # Distinguish "next" and "prev" gestures from the "liked" gesture
    if mcp_y_avg < 0.5:
        if handedness == "Right" and not (thumb_up and index_down and middle_down and ring_down and pinky_down):
            return "next"
        elif handedness == "Left" and not (thumb_up and index_down and middle_down and ring_down and pinky_down):
            return "prev"

    return "none"

def generate_frames():
    global liked_state, liked_timestamp
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)

        if result.multi_hand_landmarks and result.multi_handedness:
            for hand_landmarks, hand_handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                landmarks = hand_landmarks.landmark
                handedness = hand_handedness.classification[0].label
                gesture = recognize_gesture(landmarks, handedness)
                
                if gesture == "liked" and (time.time() - liked_timestamp > 1):
                    liked_state = not liked_state
                    liked_timestamp = time.time()

                if not liked_state:
                    if gesture == "next":
                        pyautogui.press('right')
                        time.sleep(0.5)
                    elif gesture == "prev":
                        pyautogui.press('left')
                        time.sleep(0.5)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    socketio.run(app, debug=True)
