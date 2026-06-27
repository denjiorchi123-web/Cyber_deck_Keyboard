import usb_hid
import board
import digitalio
import storage
import time

# Add a small delay to let the power and pins settle before reading the button
time.sleep(0.1)

# Set up the joystick click button (GP28) as a boot bypass key
bypass = digitalio.DigitalInOut(board.GP28)
bypass.direction = digitalio.Direction.INPUT
bypass.pull = digitalio.Pull.UP

# If joystick click is NOT held down (value is True), disable the USB Drive
# We do NOT disable the serial port (usb_cdc) so that you can always edit files via Thonny as a backup!
if bypass.value:
    storage.disable_usb_drive()

# Enable standard keyboard, mouse, and consumer control HID devices
usb_hid.enable((
    usb_hid.Device.KEYBOARD,
    usb_hid.Device.MOUSE,
    usb_hid.Device.CONSUMER_CONTROL,
))
