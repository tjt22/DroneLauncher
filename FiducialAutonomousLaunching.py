import cv2
import numpy as np
from djitellopy import Tello
import time
import asyncio
from bleak import BleakClient
import keyboard

# BLE variables
device_address = "86:5C:88:8B:12:20"  # Replace with your peripheral's BLE address
characteristic_uuid = "19B10001-E8F2-537E-4F6C-D104768A1214"  # Replace with your characteristic UUID

# Initialize the BLE client
client = None

async def toggle_characteristic(client):
    # Get the current value of the characteristic
    characteristic = await client.read_gatt_char(characteristic_uuid)

    # Convert the characteristic value to an integer
    value = int.from_bytes(characteristic, "big")

    # Toggle the value between 0 and 1
    value = 1 - value
    print(f"Value: {value}")
    # Write the new value to the characteristic
    await client.write_gatt_char(characteristic_uuid, value.to_bytes(1, "big"))
    if value == 1:
        print("Launcher activated")
    else:
        print("Launcher deactivated")

async def check_bluetooth_connection():
    global client
    client = BleakClient(device_address)
    try:
        await client.connect()
        is_connected = await client.is_connected()
        if is_connected:
            print("Bluetooth connected successfully.")
        else:
            print("Failed to connect Bluetooth.")
        return is_connected
    except Exception as e:
        print(f"Error connecting to Bluetooth: {e}")
        return False

def get_marker_center_and_size(corners):
    marker_corners = corners.reshape(4, 2)
    center_x_marker = int(np.mean(marker_corners[:, 0]))
    center_y_marker = int(np.mean(marker_corners[:, 1]))
    side_lengths = [np.linalg.norm(marker_corners[i] - marker_corners[(i + 1) % 4]) for i in range(4)]
    marker_size = np.mean(side_lengths)
    return center_x_marker, center_y_marker, marker_size

async def main():
    # Check Bluetooth connection
    connected = await check_bluetooth_connection()

    if connected:
        # Initialize Tello
        drone = Tello()
        drone.connect()
        print(f"Battery: {drone.query_battery()}%")
        drone.streamon()
        drone.takeoff()
        time.sleep(2)

        # Register a spacebar keypress event to call the toggle_characteristic function
        keyboard.add_hotkey("space", lambda: asyncio.run(toggle_characteristic(client)))

        text = ""
        marker_sizeThreshold = 105  # The size threshold for the marker
        MARGIN = 10  # Margin for centering
        Y_Margin = MARGIN  # Use a consistent margin for vertical centering

        # Load the dictionary that was used to generate the ArUco markers
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        parameters = cv2.aruco.DetectorParameters()

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

                    # Debugging: print current status
                    print(f"Marker size: {marker_size}, Diff X: {diff_x}, Diff Y: {diff_y}")

                    if marker_size >= marker_sizeThreshold:
                        # Ensure the marker is centered before landing
                        if abs(diff_x) <= MARGIN and abs(diff_y) <= Y_Margin:
                            action_text = "Marker centered, landing"
                            print(action_text)  # Debugging: print action
                            drone.send_rc_control(0, 0, 0, 0)
                            time.sleep(2)  # Delay after command
                            action_text = "Marker size threshold reached, updating BLE characteristic"
                            print(action_text)  # Debugging: print action
                            await toggle_characteristic(client)  # Update BLE characteristic
                            time.sleep(1.5)
                            drone.emergency()  # Land the drone
                            time.sleep(2)  # Delay after landing command
                            await toggle_characteristic(client)  # Update BLE characteristic
                            break  # Exit the loop after landing
                        else:
                            action_text = "Centering marker before landing"
                            print(action_text)  # Debugging: print action

                            # Adjust the drone's position to center the marker
                            if abs(diff_x) > MARGIN:
                                if diff_x > 0:
                                    action_text += " | Moving right"
                                    drone.send_rc_control(20, 0, 0, 0)  # Move right
                                else:
                                    action_text += " | Moving left"
                                    drone.send_rc_control(-20, 0, 0, 0)  # Move left
                                time.sleep(0.05)  # Delay after movement command

                            if abs(diff_y) > Y_Margin:
                                if diff_y > 0:
                                    action_text += " | Moving down"
                                    drone.send_rc_control(0, 0, -20, 0)  # Move down
                                else:
                                    action_text += " | Moving up"
                                    drone.send_rc_control(0, 0, 20, 0)  # Move up
                                time.sleep(0.05)  # Delay after movement command

                    else:
                        # If the marker is not large enough, move toward it
                        action_text = "Approaching marker"
                        print(action_text)  # Debugging: print action

                        if abs(diff_x) > MARGIN:
                            if diff_x > 0:
                                action_text += " | Moving right"
                                drone.send_rc_control(20, 20, 0, 0)  # Move right
                            else:
                                action_text += " | Moving left"
                                drone.send_rc_control(-20, 20, 0, 0)  # Move left
                            time.sleep(0.05)  # Delay after movement command

                        if abs(diff_y) > Y_Margin:
                            if diff_y > 0:
                                action_text += " | Moving down"
                                drone.send_rc_control(0, 20, -20, 0)  # Move down
                            else:
                                action_text += " | Moving up"
                                drone.send_rc_control(0, 20, 20, 0)  # Move up
                            time.sleep(0.05)  # Delay after movement command

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
            # Ensure to properly disconnect and clean up
            drone.streamoff()
            cv2.destroyAllWindows()
            if client and client.is_connected:
                await client.disconnect()

# Run the main function
asyncio.run(main())
