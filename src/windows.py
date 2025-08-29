"""Windows 専用のウィンドウ操作ユーティリティ。

ctypes を用いて Win32 API を直接呼び出すため、追加依存を増やさない。
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass

if sys.platform != "win32":  # 実行時ガード
    raise RuntimeError("このモジュールは Windows でのみ使用できます")

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


# DPI 認識を有効化（スケーリング環境での座標ずれ対策）
try:
    user32.SetProcessDPIAware()
except Exception:
    pass


@dataclass(frozen=True)
class Rect:
    """矩形。left/top/right/bottom。"""

    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)


def _get_window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def _is_window_visible(hwnd: int) -> bool:
    return bool(user32.IsWindowVisible(hwnd))


def find_window_by_partial_title(partial: str) -> int | None:
    """タイトルに部分一致する最前面のウィンドウを探す。

    Args:
        partial: 部分一致させるタイトル文字列。

    Returns:
        見つかったウィンドウのハンドル（見つからなければ ``None``）。
    """
    matched: int | None = None

    @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int)
    def enum_proc(hwnd: int, lparam: int) -> int:
        nonlocal matched
        if not _is_window_visible(hwnd):
            return 1
        title = _get_window_text(hwnd)
        if partial in title:
            matched = hwnd
            return 0  # stop
        return 1  # continue

    user32.EnumWindows(enum_proc, 0)
    return matched


def bring_to_foreground(hwnd: int) -> None:
    """対象ウィンドウをアクティブ化して前面へ。"""
    SW_RESTORE = 9
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)


def get_window_rect(hwnd: int) -> Rect:
    """ウィンドウ全体のスクリーン座標での矩形を取得。"""
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return Rect(left=rect.left, top=rect.top, right=rect.right, bottom=rect.bottom)


def click_screen(x: int, y: int) -> None:
    """スクリーン座標 ``(x, y)`` を左クリック。"""
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    user32.SetCursorPos(int(x), int(y))
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.03)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
