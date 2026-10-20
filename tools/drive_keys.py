#!/usr/bin/env python3
"""Drive the running port with a virtual keyboard, so a test can reach real gameplay.

There is no ydotool/wtype/xdotool on this box, and the game takes focus when it is
launched, so keys sent through a /dev/uinput virtual keyboard land in it. The host
sees them both as ImGui keys (F1/F2/F3) and through SDL_GetKeyboardState, which is
the keyboard-as-pad layer in src/common/input_kbm.cpp.

    tools/drive_keys.py START START A A RIGHT RIGHT RIGHT A A
    tools/drive_keys.py --delay 1.2 F1
    tools/drive_keys.py --wait 12 START           # wait before the first press

Token names are the pad actions, not key names: START ENTER A B UP DOWN LEFT RIGHT
F1 F2 F3 ESC TAB, plus SLEEP:<seconds>. The mapping is the one input_kbm.cpp
implements: Enter = Start, Space = A, Escape = B, arrows = D-pad, Tab = Back.
"""
import sys
import time

from evdev import UInput, ecodes as e

KEYS = {
    "START": e.KEY_ENTER, "ENTER": e.KEY_ENTER,
    "A": e.KEY_SPACE,
    "B": e.KEY_ESC, "ESC": e.KEY_ESC,
    "BACK": e.KEY_TAB, "TAB": e.KEY_TAB,
    "UP": e.KEY_UP, "DOWN": e.KEY_DOWN, "LEFT": e.KEY_LEFT, "RIGHT": e.KEY_RIGHT,
    "F1": e.KEY_F1, "F2": e.KEY_F2, "F3": e.KEY_F3,
}


def main(argv):
    delay, wait, tokens = 0.9, 0.0, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--delay":
            delay = float(argv[i + 1]); i += 2
        elif a == "--wait":
            wait = float(argv[i + 1]); i += 2
        else:
            tokens.append(a.upper()); i += 1
    if not tokens:
        print(__doc__, file=sys.stderr)
        return 2

    unknown = [t for t in tokens if t not in KEYS and not t.startswith("SLEEP:")]
    if unknown:
        print(f"unknown token(s): {' '.join(unknown)}", file=sys.stderr)
        return 2

    with UInput({e.EV_KEY: sorted(set(KEYS.values()))}, name="sims1-drive-kbd") as ui:
        time.sleep(max(wait, 1.0))  # the device needs a moment to be picked up
        for t in tokens:
            if t.startswith("SLEEP:"):
                time.sleep(float(t.split(":", 1)[1]))
                continue
            code = KEYS[t]
            ui.write(e.EV_KEY, code, 1); ui.syn()
            time.sleep(0.13)                      # a real press, not a glitch
            ui.write(e.EV_KEY, code, 0); ui.syn()
            print(f"pressed {t}", flush=True)
            time.sleep(delay)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
