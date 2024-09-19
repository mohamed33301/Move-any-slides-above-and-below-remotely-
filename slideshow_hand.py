import cv2
import mediapipe as mp
import pyautogui
import time
import os

# Initialize MediaPipe Hands.
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Function to recognize gestures.
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

# Function to open PowerPoint presentation and start slideshow
def open_presentation(file_path):
    if os.path.exists(file_path):
        os.startfile(file_path)
        # Wait a few seconds to allow PowerPoint to open
        time.sleep(5)
        # Start the slideshow
        pyautogui.hotkey('f5')
    else:
        print("File not found.")

# Path to your PowerPoint file
pptx_file_path = "D:/Downloads/[CC_23] Lab 1.pptx"

# Open the PowerPoint presentation
open_presentation(pptx_file_path)

# State variable to track the "liked" gesture
liked_state = False
liked_timestamp = time.time()

# Start capturing video from webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally for natural (selfie-view) visualization.
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # Convert the BGR image to RGB.
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks and result.multi_handedness:
        for hand_landmarks, hand_handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            # Draw hand landmarks.
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            landmarks = hand_landmarks.landmark
            handedness = hand_handedness.classification[0].label
            gesture = recognize_gesture(landmarks, handedness)
            
            if gesture == "liked" and (time.time() - liked_timestamp > 1):  # Debounce like gesture
                liked_state = not liked_state  # Toggle the liked state
                print("Like gesture detected, toggling liked state to", liked_state)
                liked_timestamp = time.time()  # Update the timestamp
            
            # Only change slides if liked_state is False
            if not liked_state:
                if gesture == "next":
                    print("Next gesture detected")
                    pyautogui.press('right')
                    time.sleep(0.5)  # Adjust delay if necessary
                elif gesture == "prev":
                    print("Previous gesture detected")
                    pyautogui.press('left')
                    time.sleep(0.5)  # Adjust delay if necessary

    # Display the frame
    cv2.imshow("Hand Gesture Control", frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
