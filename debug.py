"""
5秒待機後、アクティブ（前面）ウィンドウの左上から
相対座標 x=400, y=220 の位置で「左クリック」を実行します。
Windows での実行を想定しています。

外部依存はなく、ctypes 経由で Win32 API を使用します。
"""

from __future__ import annotations

import platform
import sys
import time


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

    # マウスイベントフラグ（左クリック）
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

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

    # 現在のカーソル位置で左クリックを実行
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    return 0


if __name__ == "__main__":
    sys.exit(main())
