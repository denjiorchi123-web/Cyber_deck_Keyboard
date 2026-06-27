# Row wire -> Pin1 -> [2-pin Switch] -> Pin2 -> Anode -> [1N4148] -> Cathode (banded end) -> Column wire
# Cathode (black banded end) faces the COLUMN side

import board
import analogio
import digitalio
import time
from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC, AX, Key
from kmk.scanners import DiodeOrientation
from kmk.modules import Module
from kmk.modules.mouse_keys import MouseKeys
from kmk.modules.layers import Layers
from kmk.extensions.media_keys import MediaKeys

class AnalogJoystick(Module):
    def __init__(self, invert_x=False, invert_y=False, dead_zone=2000, max_speed=20, exponent=2.2, scroll_sensitivity=0.08, poll_ms=10):
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.dead_zone = dead_zone
        self.max_speed = max_speed
        self.exponent = exponent
        self.scroll_sensitivity = scroll_sensitivity
        self.poll_interval = poll_ms / 1000.0  # convert to seconds

        # Initialize Analog Joystick inputs
        # VRx on GP26 (ADC0), VRy on GP27 (ADC1)
        self.x_axis = analogio.AnalogIn(board.GP26)
        self.y_axis = analogio.AnalogIn(board.GP27)

        # SW (click) on GP28 with pull-up resistor (LOW = pressed)
        self.click = digitalio.DigitalInOut(board.GP28)
        self.click.direction = digitalio.Direction.INPUT
        self.click.pull = digitalio.Pull.UP

        # Sub-pixel accumulators for ultra-precise slow movement
        self.remainder_x = 0.0
        self.remainder_y = 0.0

        # Sub-pixel scroll accumulators
        self.remainder_scroll_x = 0.0
        self.remainder_scroll_y = 0.0

        # Calibrate center resting position at boot
        self.center_x = 32768
        self.center_y = 32768
        self.calibrate()

        self.last_poll_time = time.monotonic()

    def calibrate(self):
        # Average 20 readings to establish true center and avoid drift
        sum_x = 0
        sum_y = 0
        for _ in range(20):
            sum_x += self.x_axis.value
            sum_y += self.y_axis.value
            time.sleep(0.005)
        self.center_x = int(sum_x / 20)
        self.center_y = int(sum_y / 20)

    def during_bootup(self, keyboard):
        pass

    def before_hid_send(self, keyboard):
        pass

    def after_hid_send(self, keyboard):
        pass

    def before_matrix_scan(self, keyboard):
        now = time.monotonic()
        if now - self.last_poll_time >= self.poll_interval:
            self.last_poll_time = now

            # Poll mouse click button (active-low)
            # Check if Layer 1 is active (Fn key is held down)
            is_fn_held = 1 in keyboard.active_layers

            if not self.click.value:
                if is_fn_held:
                    # Trigger Right Mouse Button
                    if KC.MB_RMB not in keyboard.keys_pressed:
                        keyboard.keys_pressed.add(KC.MB_RMB)
                        keyboard.hid_pending = True
                    # Discard Left Click if it was active
                    if KC.MB_LMB in keyboard.keys_pressed:
                        keyboard.keys_pressed.discard(KC.MB_LMB)
                        keyboard.hid_pending = True
                else:
                    # Trigger Left Mouse Button
                    if KC.MB_LMB not in keyboard.keys_pressed:
                        keyboard.keys_pressed.add(KC.MB_LMB)
                        keyboard.hid_pending = True
                    # Discard Right Click if it was active
                    if KC.MB_RMB in keyboard.keys_pressed:
                        keyboard.keys_pressed.discard(KC.MB_RMB)
                        keyboard.hid_pending = True
            else:
                # Release both buttons when joystick SW is released
                changed = False
                if KC.MB_LMB in keyboard.keys_pressed:
                    keyboard.keys_pressed.discard(KC.MB_LMB)
                    changed = True
                if KC.MB_RMB in keyboard.keys_pressed:
                    keyboard.keys_pressed.discard(KC.MB_RMB)
                    changed = True
                if changed:
                    keyboard.hid_pending = True

            # Read analog values
            x_val = self.x_axis.value
            y_val = self.y_axis.value

            # Swap axes to match physical orientation:
            # Physical Y (up/down) -> Screen X (left/right)
            # Physical X (left/right) -> Screen Y (up/down)
            dx_raw = self._calculate_speed(y_val, self.center_y)
            dy_raw = self._calculate_speed(x_val, self.center_x)

            # Apply invert flags
            if self.invert_x:
                dx_raw = -dx_raw
            if self.invert_y:
                dy_raw = -dy_raw

            if is_fn_held:
                # SCROLLING MODE (Fn is held down)
                # Scroll vertically using native AX.W (Axis code 2)
                # Scroll horizontally using native AX.P (Axis code 3)
                self.remainder_scroll_x += dx_raw * self.scroll_sensitivity
                self.remainder_scroll_y += -dy_raw * self.scroll_sensitivity

                scroll_x = int(self.remainder_scroll_x)
                scroll_y = int(self.remainder_scroll_y)

                self.remainder_scroll_x -= scroll_x
                self.remainder_scroll_y -= scroll_y

                # Trigger analog scrolling if displacement is non-zero
                if scroll_y != 0:
                    AX.W.move(keyboard, scroll_y)
                if scroll_x != 0:
                    AX.P.move(keyboard, scroll_x)
            else:
                # CURSOR MOVEMENT MODE (Fn is released)
                self.remainder_x += dx_raw
                self.remainder_y += dy_raw

                dx = int(self.remainder_x)
                dy = int(self.remainder_y)

                self.remainder_x -= dx
                self.remainder_y -= dy

                # Move mouse cursor if displacement is non-zero
                if dx != 0:
                    AX.X.move(keyboard, dx)
                if dy != 0:
                    AX.Y.move(keyboard, dy)

    def after_matrix_scan(self, keyboard):
        pass

    def on_powersave_enable(self, keyboard):
        pass

    def on_powersave_disable(self, keyboard):
        pass

    def _calculate_speed(self, value, center):
        min_val = 0
        max_val = 65535
        
        if value > center + self.dead_zone:
            # Scale deflection between 0.0 and 1.0 past the dead-zone edge
            deflection = (value - (center + self.dead_zone)) / (max_val - (center + self.dead_zone))
            # Exponential precision response curve
            return (deflection ** self.exponent) * self.max_speed
        elif value < center - self.dead_zone:
            # Scale deflection between 0.0 and 1.0 past the dead-zone edge
            deflection = ((center - self.dead_zone) - value) / ((center - self.dead_zone) - min_val)
            # Exponential precision response curve (negative direction)
            return -((deflection ** self.exponent) * self.max_speed)
        return 0.0

# Custom keys for Volume/Brightness dual functions (Volume by default, Brightness with Shift)
def vol_brt_up_on_press(key, keyboard, *args):
    is_shift = KC.LSFT in keyboard.keys_pressed or KC.RSFT in keyboard.keys_pressed
    if is_shift:
        keyboard.keys_pressed.add(KC.BRIU)
    else:
        keyboard.keys_pressed.add(KC.VOLU)
    keyboard.hid_pending = True

def vol_brt_up_on_release(key, keyboard, *args):
    keyboard.keys_pressed.discard(KC.BRIU)
    keyboard.keys_pressed.discard(KC.VOLU)
    keyboard.hid_pending = True

KC_VOL_BRT_UP = Key(on_press=vol_brt_up_on_press, on_release=vol_brt_up_on_release)


def vol_brt_dn_on_press(key, keyboard, *args):
    is_shift = KC.LSFT in keyboard.keys_pressed or KC.RSFT in keyboard.keys_pressed
    if is_shift:
        keyboard.keys_pressed.add(KC.BRID)
    else:
        keyboard.keys_pressed.add(KC.VOLD)
    keyboard.hid_pending = True

def vol_brt_dn_on_release(key, keyboard, *args):
    keyboard.keys_pressed.discard(KC.BRID)
    keyboard.keys_pressed.discard(KC.VOLD)
    keyboard.hid_pending = True

KC_VOL_BRT_DN = Key(on_press=vol_brt_dn_on_press, on_release=vol_brt_dn_on_release)

# Mic Mute macro shortcut (Ctrl+Shift+M for Teams/Zoom/Discord)
KC_MIC_MUTE = KC.LCTL(KC.LSFT(KC.M))

# Webcam toggle macro shortcut (Alt+V for Zoom video)
KC_CAM_TOGGLE = KC.LALT(KC.V)

# Initialize Keyboard object
keyboard = KMKKeyboard()

# GPIO Row & Column Setup (GP5 is skipped)
keyboard.row_pins = (board.GP0, board.GP1, board.GP2, board.GP3, board.GP4)
keyboard.col_pins = (
    board.GP6,  board.GP7,  board.GP8,  board.GP9,  board.GP10,
    board.GP11, board.GP12, board.GP13, board.GP14, board.GP15,
)

# Diode orientation
# Electrically, active-low pull-up configuration (COL2ROW) is what registers key presses.
keyboard.diode_orientation = DiodeOrientation.COL2ROW

# Add Layers module for multi-layer support
keyboard.modules.append(Layers())

# Add MouseKeys module so mouse click keycodes are registered and HID reporting is configured
keyboard.modules.append(MouseKeys())

# Add MediaKeys extension for volume and brightness control
keyboard.extensions.append(MediaKeys())

# Add Custom Analog Joystick Module
keyboard.modules.append(AnalogJoystick(
    invert_x=False,
    invert_y=True,
    dead_zone=2000,
    max_speed=6,      # Decreased to 6 for a very slow, high-precision cursor speed
    exponent=3.0,      # Increased to 3.0 for extremely fine control at low deflection
    poll_ms=10
))

# 2-Layer Keymap: 5 rows x 10 columns = 50 keys per layer
keyboard.keymap = [
    # ─── Layer 0 — Base ───────────────────────────────────────────────
    [
        # R1:  1        2        3        4        5        6        7        8        9        0
               KC.N1,   KC.N2,   KC.N3,   KC.N4,   KC.N5,   KC.N6,   KC.N7,   KC.N8,   KC.N9,   KC.N0,
        # R2:  Q        W        E        R        T        Y        U        I        O        P
               KC.Q,    KC.W,    KC.E,    KC.R,    KC.T,    KC.Y,    KC.U,    KC.I,    KC.O,    KC.P,
        # R3:  A        S        D        F        G        H        J        K        L        ENTER
               KC.A,    KC.S,    KC.D,    KC.F,    KC.G,    KC.H,    KC.J,    KC.K,    KC.L,    KC.ENT,
        # R4:  Z        X        C        V        B        N        M        ,        .        /
               KC.Z,    KC.X,    KC.C,    KC.V,    KC.B,    KC.N,    KC.M,    KC.COMM, KC.DOT,  KC.SLSH,
        # R5:  CTRL     SHIFT    ALT      SPACE    SPACE    SPACE    MO(1)    CAPS     BSPC     DEL
               KC.LCTL, KC.LSFT, KC.LALT, KC.SPC,  KC.SPC,  KC.SPC,  KC.MO(1),KC.CAPS, KC.BSPC, KC.DEL,
    ],

    # ─── Layer 1 — Fn (hold MO(1) / Fn to access) ──────────────────────
    [
        # R1:  F1       F2       F3       F4       F5       F6       F7       F8       F9       F10
               KC.F1,   KC.F2,   KC.F3,   KC.F4,   KC.F5,   KC.F6,   KC.F7,   KC.F8,   KC.F9,   KC.F10,
        # R2:  `        UP       VOL_UP   VOL_DN   PGUP     F11      F12      =        [        ]
               KC.GRV,  KC.UP,   KC_VOL_BRT_UP, KC_VOL_BRT_DN, KC.PGUP, KC.F11, KC.F12, KC.EQL, KC.LBRC, KC.RBRC,
        # R3:  LEFT     DOWN     RIGHT    \        PGDN     HOME     +        ;        :        ENTER
               KC.LEFT, KC.DOWN, KC.RGHT, KC.BSLS, KC.PGDN, KC.HOME, KC.PLUS, KC.SCLN, KC.COLN, KC.TRNS,
        # R4:  ESC      TAB      CAM      '        PTR      END      -        ---      ---      ---
               KC.ESC,  KC.TAB,  KC_CAM_TOGGLE, KC.QUOT, KC.PSCR, KC.END,  KC.MINS, KC.TRNS, KC.TRNS, KC.TRNS,
        # R5:  CTRL     SHIFT    ALT      MUTE     MUTE     MUTE     Fn       ESC      ---      ---
               KC.TRNS, KC.TRNS, KC.TRNS, KC_MIC_MUTE, KC_MIC_MUTE, KC_MIC_MUTE, KC.TRNS, KC.ESC, KC.TRNS, KC.TRNS,
    ],
]

if __name__ == '__main__':
    keyboard.go()
