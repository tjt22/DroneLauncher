# DroneLauncher

A central and peripheral BLE software that launches a tether whenever spacebar is pressed. 

# Setup
*Python*
Install the following libraries:
asyncio
bleak
keyboard

*Arduino*
Follow the setup instructions on this tutorial for the Seeed XIAO nRF52840 (Sense) using the Arduino IDE:
https://wiki.seeedstudio.com/XIAO_BLE/

Make sure that you select the Seeed XIAO nRF52840 BLE Sense from the mBed board manager before you compile

You can test this code with any mobile BLE scanner. Just change the characteristic value to 0 or 1

# Actual Use
1. Upload DroneLauncherFirmware.ino to the board
2. Power the board from external power and wire your circuit
3. Run the AutoLaunchInput.py script and make sure your laptop bluetooth is on
4. Press spacebar to turn on or off the motor

