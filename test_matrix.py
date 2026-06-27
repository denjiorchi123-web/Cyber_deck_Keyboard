# Custom Keyboard Matrix Diagnostic Tool
# Diode Wiring Direction Reference:
# Row wire -> Pin1 -> [2-pin Switch] -> Pin2 -> Anode -> [1N4148] -> Cathode (banded end) -> Column wire

import board
import digitalio
import time

# Pin assignments from user specification
ROW_PINS = [board.GP0, board.GP1, board.GP2, board.GP3, board.GP4]
COL_PINS = [
    board.GP6, board.GP7, board.GP8, board.GP9, board.GP10,
    board.GP11, board.GP12, board.GP13, board.GP14, board.GP15
]

print("--- Keyboard Matrix Diagnostic Script ---")
print("This script will check the matrix in both Active-Low (Pull-Up) and Active-High (Pull-Down) modes.")
print("Drop this file as 'code.py' on your CIRCUITPY drive to run it.")
print("Open a serial console (REPL) to view the output.\n")

last_idle_print = 0

def scan_matrix(active_low=True):
    # Initialize row pins
    rows = []
    for pin in ROW_PINS:
        r = digitalio.DigitalInOut(pin)
        r.direction = digitalio.Direction.OUTPUT
        # Active-low: idle rows are HIGH (True)
        # Active-high: idle rows are LOW (False)
        r.value = True if active_low else False
        rows.append(r)
        
    # Initialize column pins
    cols = []
    for pin in COL_PINS:
        c = digitalio.DigitalInOut(pin)
        c.direction = digitalio.Direction.INPUT
        # Active-low: pull-up
        # Active-high: pull-down
        c.pull = digitalio.Pull.UP if active_low else digitalio.Pull.DOWN
        cols.append(c)
        
    # Read column idle states before driving rows active
    idle_states = [c.value for c in cols]
    
    detected = []
    # Scan the matrix
    for r_idx, r in enumerate(rows):
        # Activate the row
        # Active-low: drive row LOW (False)
        # Active-high: drive row HIGH (True)
        r.value = False if active_low else True
        time.sleep(0.002)  # Settle time
        
        for c_idx, c in enumerate(cols):
            # In active-low: key press pulls column LOW (False)
            # In active-high: key press pulls column HIGH (True)
            pressed = (not c.value) if active_low else c.value
            
            # If the column is in its active state (different from idle state), register it
            # But only if it's not a shorted column (i.e. the idle state wasn't already the active state)
            c_idle = idle_states[c_idx]
            if pressed and (c_idle == (True if active_low else False)):
                detected.append((r_idx, c_idx))
                
        # Return row to idle state
        r.value = True if active_low else False
        
    # De-initialize pins to free them for subsequent scans
    for r in rows:
        r.deinit()
    for c in cols:
        c.deinit()
        
    return idle_states, detected

while True:
    now = time.monotonic()
    
    # Run scans for both modes
    try:
        idle_low, pressed_low = scan_matrix(active_low=True)
        idle_high, pressed_high = scan_matrix(active_low=False)
    except Exception as e:
        print(f"Error scanning: {e}")
        time.sleep(1)
        continue
    
    # Print key detections immediately
    for r, c in pressed_low:
        print(f"[ACTIVE-LOW] KEY DETECTED -> Row {r} Col {c} (GP{r} -> GP{c+6})")
        
    for r, c in pressed_high:
        print(f"[ACTIVE-HIGH] KEY DETECTED -> Row {r} Col {c} (GP{r} -> GP{c+6})")
        
    # Print idle states and heartbeat every 2 seconds
    if now - last_idle_print >= 2.0:
        print("\n--- Idle States (Heartbeat) ---")
        low_str = "".join(["1" if v else "0" for v in idle_low])
        high_str = "".join(["1" if v else "0" for v in idle_high])
        print(f"Active-Low (Pull-Up) Col Idle States (should be 1111111111): {low_str}")
        print(f"Active-High (Pull-Down) Col Idle States (should be 0000000000): {high_str}")
        
        # Diagnostics for shorted pins
        for i, val in enumerate(idle_low):
            if not val:
                print(f"  WARNING: Col {i} (GP{COL_PINS[i]}) is LOW at idle in Pull-Up mode. Possible short to GND!")
        for i, val in enumerate(idle_high):
            if val:
                print(f"  WARNING: Col {i} (GP{COL_PINS[i]}) is HIGH at idle in Pull-Down mode. Possible short to VCC!")
                
        last_idle_print = now
        
    # Small delay between full matrix scans to prevent CPU thrashing
    time.sleep(0.05)
