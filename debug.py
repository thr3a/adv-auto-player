"""
Wait 5 seconds, then right-click at a position relative to the
currently active (foreground) window: x=400, y=220 from the window's
top-left corner. Intended to run on Windows.

No external dependencies; uses Win32 APIs via ctypes.
"""

from __future__ import annotations

import sys
import time
import platform


def main() -> int:
    if platform.system() != "Windows":
        print("This script is intended to run on Windows.")
        return 1

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    # Try to be DPI-aware so window coordinates match physical pixels
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass

    # Win32 RECT struct
    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    # Mouse event flags
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010

    # Wait 5 seconds
    time.sleep(5)

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        print("Could not get foreground window handle.")
        return 2

    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        print("GetWindowRect failed.")
        return 3

    # Target position relative to the active window
    target_x = int(rect.left + 400)
    target_y = int(rect.top + 220)

    if not user32.SetCursorPos(target_x, target_y):
        print("SetCursorPos failed.")
        return 4

    # Perform right-click at the current cursor position
    user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

    return 0


if __name__ == "__main__":
    sys.exit(main())

