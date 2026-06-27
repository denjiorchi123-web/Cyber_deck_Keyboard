# Cyberdeck Keyboard Firmware

This repository contains the KMK-based custom firmware for the Cyberdeck Keyboard, built on a Raspberry Pi Pico (RP2040).

## Features
- **KMK Firmware**: Keyboard layout configuration using CircuitPython.
- **Custom Analog Joystick**: Direct analog joystick integration for high-precision mouse cursor movement, left/right clicks, and analog scrolling.
- **Dual-Function Media Keys**: Context-aware Volume and Brightness adjustment.
- **Application Toggles**: Dedicated microphone mute and webcam toggles.
- **USB Write Protection Lockout**: Built-in developer bypass switch to hide/reveal the USB drive.

---

## Hardware Configuration (Pico Pins)
- **Rows**: `GP0`, `GP1`, `GP2`, `GP3`, `GP4`
- **Columns**: `GP6`, `GP7`, `GP8`, `GP9`, `GP10`, `GP11`, `GP12`, `GP13`, `GP14`, `GP15` (GP5 skipped)
- **Joystick X/Y**: `GP26` (VRx), `GP27` (VRy)
- **Joystick Click (SW)**: `GP28`

---

## Keyboard Layout & Key Mappings

### Base Layer (Normal Typing)
Standard 50-key matrix layout mapping. Normal keys function as expected.

### Fn Layer (Hold Fn to access)
To access the secondary layout, **hold down the `Fn` key** (7th key in the bottom row, next to Caps) and press the target key:

| Target Function | Combination | What it does |
| :--- | :--- | :--- |
| **Volume Up** | Hold `Fn` + press `E` | Increases system volume |
| **Volume Down** | Hold `Fn` + press `R` | Decreases system volume |
| **Brightness Up** | Hold `Fn` + Hold `Shift` + press `E` | Increases screen brightness |
| **Brightness Down** | Hold `Fn` + Hold `Shift` + press `R` | Decreases screen brightness |
| **Microphone Mute/Unmute** | Hold `Fn` + press `Spacebar` | Mutes/unmutes mic in Zoom, Teams, Discord (sends `Ctrl + Shift + M`) |
| **Camera Toggle** | Hold `Fn` + press `C` | Toggles webcam in Zoom (sends `Alt + V`) |
| **Backslash (`\`)** | Hold `Fn` + press `F` | Types `\` |
| **Plus (`+`)** | Hold `Fn` + press `J` | Types `+` |
| **Semicolon (`;`)** | Hold `Fn` + press `K` | Types `;` |
| **Colon (`:`)** | Hold `Fn` + press `L` | Types `:` |
| **Equal (`=`)** | Hold `Fn` + press `I` | Types `=` |
| **Tab** | Hold `Fn` + press `X` | Sends `Tab` |
| **Escape** | Hold `Fn` + press `Caps` | Sends `Esc` |
| **Print Screen** | Hold `Fn` + press `B` | Takes a screenshot (sends Print Screen) |
| **Joystick Mouse Movement** | Move joystick | Moves the mouse cursor very slowly and precisely |
| **Joystick Mouse Scroll** | Hold `Fn` + move joystick | Scrolls vertically (up/down) and horizontally (left/right) |
| **Left Click** | Click/press down joystick | Left click |
| **Right Click** | Hold `Fn` + click/press down joystick | Right click |

---

## Installation & Configuration Guide

### Step 1: Install CircuitPython on your Pico
1. Download the latest CircuitPython `.uf2` file for the **Raspberry Pi Pico** from [circuitpython.org](https://circuitpython.org/board/raspberry_pi_pico/).
2. Unplug your Pico's USB cable.
3. Hold down the **BOOTSEL** button on the Pico.
4. While holding the button, plug the USB cable back into your computer.
5. A drive named **RPI-RP2** will appear. Drag and drop the downloaded `.uf2` file onto it.
6. The Pico will reboot and mount as a new drive named **CIRCUITPY**.

### Step 2: Copy Firmware and Configuration Files
Copy the following files/folders directly onto your **CIRCUITPY** drive:
- `code.py` (Main keyboard firmware file)
- `boot.py` (USB lockout security file)
- `kmk/` folder (The core KMK library folder containing `keys.py`, `kmk_keyboard.py`, etc.)

---

## Developer Security Mode (Bypassing USB Lockout)

For security, the `boot.py` file automatically **disables the USB mass storage drive** so that others cannot easily plug in the keyboard and modify your code.

### To unlock/edit your code again:
1. Unplug the keyboard.
2. **Press and hold down the joystick click button** (GP28).
3. Plug the USB cable back in while keeping the joystick button pressed.
4. The **CIRCUITPY** drive will now show up on your computer, allowing you to update or modify `code.py`.

---

## Recovery / Factory Reset
If the keyboard gets locked out or the drive doesn't appear, perform a full reset:
1. Download the official **[flash_nuke.uf2](https://datasheets.raspberrypi.com/soft/flash_nuke.uf2)** file.
2. Plug the Pico in while holding the **BOOTSEL** button.
3. Drag and drop `flash_nuke.uf2` onto the **RPI-RP2** drive.
4. Let the board clear its memory and reboot back to bootloader mode.
5. Re-flash CircuitPython and copy your files.
