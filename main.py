import osascript
import cv2
from cvzone.HandTrackingModule import HandDetector
import time
import pyautogui
import warnings

# Suppressing UserWarnings from google.protobuf.symbol_database
warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf.symbol_database')

# Variables for screen width and height
width, height = 1280, 720

# Variables to manage skipping functionality
skipHeld = False
skipFirst = True
skipCooldown = False
coolDownTime = 0.75  # Cooldown time in seconds
skipTime = 0

# Setting up the camera
cap = cv2.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)

# Variables to track hand speed for skipping
prev_skip_time = time.time()
prev_skip_pos = None

# Variables to track hand speed for volume control
prev_volume_time = time.time()
prev_volume_pos = None
volumeFirst = True
volumeHeld = False
init_volume = 0

# Initializing the hand detector with a detection confidence of 0.8 and a maximum of 1 hand
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Function to calculate horizontal distance between two points
def calc_Xdist(point1, point2):
    return (point1[0] - point2[0])

# Function to calculate vertical distance between two points
def calc_Ydist(point1, point2):
    return (point1[1] - point2[1])

# Main loop to capture frames and detect hands
while True:
    # Read a frame from the camera and flip it horizontally
    success, img = cap.read()
    img = cv2.flip(img, 1)

    # Detect hands in the frame
    hands, img = detector.findHands(img)

    if hands:
        # Get the first visible hand
        hand = hands[0]
        fingers = detector.fingersUp(hand)  # Get the state of the fingers
        lmList = hand['lmList']  # Get the list of landmarks
        indexPosX = lmList[1][0]
        indexPosY = lmList[1][1]
        curr_index_pos = (indexPosX, indexPosY)
        curr_time = time.time()

        # Check if the hand gesture is not for skipping
        if fingers != ([0, 1, 0, 0, 0] or [1, 1, 0, 0, 0]):
            skipHeld = False
            skipFirst = True

        # Check if the hand gesture is for skipping
        if fingers == ([0, 1, 0, 0, 0] or [1, 1, 0, 0, 0]):
            skipHeld = True
            # Check if 0.01 seconds have passed
            if curr_time - prev_skip_time >= 0.01:
                if prev_skip_pos is not None:
                    # Calculate horizontal distance traveled by the index finger
                    distance = calc_Xdist(curr_index_pos, prev_skip_pos)

                    # Check if the distance traveled is significant
                    if (distance >= 35 or distance <= -35):
                        print(abs(skipTime - curr_time))

                        # Check if the cooldown period has passed
                        if abs(skipTime - curr_time) >= coolDownTime:
                            skipCooldown = False

                        # Perform the skip action if cooldown period has passed
                        if not skipCooldown:
                            skipTime = curr_time
                            skipCooldown = True
                            if distance >= 35:
                                pyautogui.press("nexttrack")  # Skip to next track
                                print("skipped")
                            else:
                                pyautogui.press("prevtrack")  # Skip to previous track
                                print("rewinded")

                # Update previous position and time for skipping
                prev_skip_pos = curr_index_pos
                prev_skip_time = curr_time

        # Reset skip variables for the first detection
        if skipFirst:
            prev_skip_time = time.time()
            prev_skip_pos = None
            skipFirst = False

        # Check if the hand gesture is not for volume control
        if fingers != ([0, 1, 1, 0, 0] or [1, 1, 1, 0, 0]):
            volumeHeld = False
            volumeFirst = True

        # Check if the hand gesture is for volume control
        if fingers == ([0, 1, 1, 0, 0] or [1, 1, 1, 0, 0]):
            volumeHeld = True

            # Initialize volume control
            if volumeFirst:
                prev_volume_pos = curr_index_pos
                volumeFirst = False
                result = osascript.osascript('get volume settings')
                volInfo = result[1].split(',')
                init_volume = volInfo[0].replace('output volume:', '')

            # Calculate vertical distance traveled by the index finger
            distance = calc_Ydist(prev_volume_pos, curr_index_pos)

            # Adjust the volume if the distance traveled is significant
            if distance >= 35 or distance <= -35:
                curr_volume = osascript.osascript('get volume settings')
                vol = "set volume output volume " + str(distance / 5 + int(init_volume))
                osascript.osascript(vol)

                # Get the current volume and print it (more debug purposes)
                result = osascript.osascript('get volume settings')
                volInfo = result[1].split(',')
                outputVol = volInfo[0].replace('output volume:', '')
                print(outputVol)

    # Display the image
    cv2.imshow("Image", img)
    key = cv2.waitKey(1)

    # Exit the loop if the escape key is pressed
    if key == 27:
        break
