import cv2
import numpy as np
from djitellopy import Tello
import time
import asyncio
from bleak import BleakClient
import keyboard

# Initialize Tello
drone = Tello()
drone.connect()
print(f"Battery: {drone.query_battery()}%")

# Start the video stream
drone.streamon()
time.sleep(2)
drone.takeoff()
drone.move_up(60)
text = ""
marker_sizeThreshold = 100  # The size threshold for the marker
MARGIN = 10  # Margin for centering

# Load the dictionary that was used to generate the ArUco markers
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters()

# BLE variables
toggle_variable = 0
address = "8F:88:67:9D:AE:AF"  # The address of the BLE peripheral
characteristic_uuid = "19B10001-E8F2-537E-4F6C-D104768A1214"  # UUID of the characteristic

# Function to calculate the center and size of the marker
def get_marker_center_and_size(corners):
    marker_corners = corners.reshape(4, 2)
    center_x_marker = int(np.mean(marker_corners[:, 0]))
    center_y_marker = int(np.mean(marker_corners[:, 1]))
    side_lengths = [np.linalg.norm(marker_corners[i] - marker_corners[(i + 1) % 4]) for i in range(4)]
    marker_size = np.mean(side_lengths)
    return center_x_marker, center_y_marker, marker_size

# Function to toggle BLE characteristic value
async def update_ble_characteristic(new_value):
    client = BleakClient(address)
    await client.connect()

    # Write the new value to the characteristic
    await client.write_gatt_char(characteristic_uuid, new_value.to_bytes(1, "big"))
    print(f"Bluetooth characteristic updated to: {new_value}")

    await client.disconnect()

# Main drone control and BLE interaction
try:
    while True:
        # Get the frame from the drone's camera
        frame = drone.get_frame_read().frame
        frame_height, frame_width, _ = frame.shape

        # Detect ArUco markers in the frame
        corners, ids, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters)
        action_text = ""

        if ids is not None:
            # Draw detected marker
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

            # Get frame and marker centers and marker size
            center_x_frame = frame_width // 2
            center_y_frame = frame_height // 2
            center_x_marker, center_y_marker, marker_size = get_marker_center_and_size(corners[0])

            # Calculate the difference between the frame center and the marker center
            diff_x = center_x_marker - center_x_frame
            diff_y = center_y_marker - center_y_frame

            # Control drone movement based on marker position
            if abs(diff_x) > MARGIN and marker_size < marker_sizeThreshold:
                if diff_x > 0:
                    action_text = "Moving right"
                    drone.send_rc_control(20, 20, 0, 0)
                else:
                    action_text = "Moving left"
                    drone.send_rc_control(-20, 20, 0, 0)

            if abs(diff_y) > MARGIN and marker_size < marker_sizeThreshold:
                if diff_y > 0:
                    action_text = "Moving down"
                    drone.send_rc_control(0, 20, -20, 0)
                else:
                    action_text = "Moving up"
                    drone.send_rc_control(0, 20, 20, 0)

            # Check if the marker size exceeds the threshold
            if marker_size >= marker_sizeThreshold:
                action_text = "Marker size threshold reached, updating BLE characteristic"
                asyncio.run(update_ble_characteristic(1))  # Update BLE characteristic to 1
                break  # Stop further movement once the threshold is reached

            # Display marker info and action
            text = f"dx: {diff_x}, dy: {diff_y}, marker size: {marker_size}"
            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.putText(frame, action_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Draw the margin rectangle
            top_left = (center_x_frame - MARGIN, center_y_frame - MARGIN)
            bottom_right = (center_x_frame + MARGIN, center_y_frame + MARGIN)
            cv2.rectangle(frame, top_left, bottom_right, (255, 0, 0), 3)

        # Display the resulting frame
        cv2.imshow('Tello Camera', frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            drone.land()
            break

finally:
    drone.land()
    drone.streamoff()
    cv2.destroyAllWindows()
