import asyncio
from bleak import BleakClient
import keyboard

# Initialize the BLE variables
device_address = "8F:88:67:9D:AE:AF"  # Replace with your peripheral's BLE address
characteristic_uuid = "19B10001-E8F2-537E-4F6C-D104768A1214"  # Replace with your characteristic UUID

async def toggle_characteristic(client):
    # Get the current value of the characteristic
    characteristic = await client.read_gatt_char(characteristic_uuid)

    # Convert the characteristic value to an integer
    value = int.from_bytes(characteristic, "big")

    # Toggle the value between 0 and 1
    value = 1 - value

    # Write the new value to the characteristic
    await client.write_gatt_char(characteristic_uuid, value.to_bytes(1, "big"))
    if (value == 1):
        print("launcher deactivated")
    elif (value == 0):
        print("launcher activated")



async def main():
    # Create a BleakClient object
    client = BleakClient(device_address)

    # Connect to the peripheral
    await client.connect()

    # Register a spacebar keypress event to call the toggle_characteristic function
    keyboard.add_hotkey("space", lambda: asyncio.run(toggle_characteristic(client)))

    print("Press the spacebar to activate or deactivate launcher")

    try:
        keyboard.wait()  # Wait for events
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.remove_hotkey("space")  # Remove the hotkey when done

    # Disconnect from the peripheral
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
