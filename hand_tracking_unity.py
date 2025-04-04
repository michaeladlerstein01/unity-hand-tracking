import cv2
import numpy as np
import socket
import mediapipe.python.solutions.hands as mp_hands
import mediapipe.python.solutions.drawing_utils as mp_drawing
import mediapipe.python.solutions.drawing_styles as mp_drawing_styles

"test1"

host, port = "127.0.0.1", 25001

def get_hand_joints(frame, hands):
    """
    Extracts hand joint positions (x, y) in the camera frame and returns a NumPy array.
    """
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    hand_positions_camera = []  # Store multiple hands if detected
    hand_positions_world = []
    hand_position_z = []

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Extract (x, y) pixel positions for all 21 landmarks
            landmarks = np.array([
                [int(landmark.x * frame.shape[1]), int(landmark.y * frame.shape[0])]
                for landmark in hand_landmarks.landmark
            ])


            hand_positions_camera.append(landmarks)

        
        # extract the z landmark separatelly,
            landmarks_z = np.array([landmark.z for landmark in hand_landmarks.landmark])






        for hand_landmarks in results.multi_hand_landmarks:
            # Extract (x, y) pixel positions for all 21 landmarks
            landmarks = np.array([
                [float(landmark.x ), float(landmark.y)]
                for landmark in hand_landmarks.landmark
            ])
            hand_positions_world.append(landmarks)
    else:
        landmarks_z = None 

    return hand_positions_camera ,  hand_positions_world ,  landmarks_z # List of NumPy arrays (one for each hand)

import cv2
import socket
import numpy as np
import mediapipe as mp

mp_hands = mp.solutions.hands

def run_hand_tracking_on_webcam():
    host, port = "127.0.0.1", 25001
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sock.connect((host, port))
        print("Connected to Unity server.")

        cap = cv2.VideoCapture(0)  # Open the webcam

        with mp_hands.Hands(
            model_complexity=0,
            max_num_hands=2,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8,
        ) as hands:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    print("Ignoring empty camera frame...")
                    continue

                # Flip once (horizontally) to mirror like a selfie
                flipped_frame = cv2.flip(frame, 1)

                # Pass the flipped frame to Mediapipe
                hand_joints, get_info , hand_z = get_hand_joints(flipped_frame, hands)

                # Draw on the flipped frame
                if hand_joints:
                    for joints in hand_joints:
                        for idx, (x, y) in enumerate(joints):
                            cv2.circle(flipped_frame, (x, y), 5, (0, 255, 0), -1)
                            cv2.putText(flipped_frame, str(idx), (x, y - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

                # Show the flipped frame
                cv2.imshow("Hand Tracking", flipped_frame)




                if hand_joints:

                    # Ensure hand_z is reshaped to (21, 1) for concatenation
                    hand_z_reshaped = hand_z.reshape(21, 1)

                    # Concatenate x, y (from joints) with z (from hand_z)
                    joints_3d = np.concatenate((joints, hand_z_reshaped), axis=1)                
                    # Send data

                    for i, joints in enumerate(joints_3d):
                        # Flatten all 21 (x, y) into a string
                        all_points = []
                        for x, y , z in joints_3d:
                            
                            all_points += [(x) / 100, (1-y) / 100 , z]   # Z is dummy for now

                        vec_str = ",".join(map(str, all_points))
                        print(f"Sending Hand {i+1} Data: {vec_str}")

                        try:
                            sock.sendall(vec_str.encode("utf-8"))
                            response = sock.recv(1024).decode("utf-8")
                            print("Unity Response:", response)
                        except (BrokenPipeError, ConnectionResetError):
                            print("Lost connection to Unity. Exiting.")
                            cap.release()
                            cv2.destroyAllWindows()
                            break

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        cap.release()
        cv2.destroyAllWindows()

    finally:
        sock.close()
        print("Socket closed.")

if __name__ == "__main__":
    run_hand_tracking_on_webcam()