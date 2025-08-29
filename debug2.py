"""
5秒待機して、現在アクティブなウィンドウのスクリーンショットを
MSS で取得し、Windows のピクチャフォルダに capture.png として保存します。

- ウィンドウ取得: PyGetWindow
- 画面キャプチャ: mss

注意:
- Windows を想定しています（macOS/Linuxでは終了）。
- 複数モニタでウィンドウが負の座標にある場合、環境によっては
  キャプチャで失敗する可能性があります（主モニタ上でお試しください）。
"""

from __future__ import annotations

import os
import platform
import sys
import time
from pathlib import Path


def get_pictures_dir() -> Path:
    r"""Windowsの既定のピクチャフォルダを返す。

    - まず Windows の Known Folder API を試行（成功すれば最も確実）。
    - 失敗した場合は %USERPROFILE%\Pictures をフォールバックとして使用。
    """
    if platform.system() != "Windows":
        # 非Windowsではホーム配下のPicturesを返すが、通常このスクリプトは使わない
        return Path.home() / "Pictures"

    # Known Folder: FOLDERID_Pictures = {33E28130-4E1E-4676-835A-98395C3BC3BB}
    try:
        import ctypes
        from ctypes import wintypes

        _ole32 = ctypes.OleDLL("ole32")
        _shell32 = ctypes.OleDLL("shell32")

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        def guid_from_str(s: str) -> GUID:
            g = GUID()
            _ole32.CLSIDFromString(wintypes.LPCWSTR(s), ctypes.byref(g))
            return g

        FOLDERID_Pictures = guid_from_str("{33E28130-4E1E-4676-835A-98395C3BC3BB}")
        ptr = ctypes.c_wchar_p()
        # SHGetKnownFolderPath(REFKNOWNFOLDERID rfid, DWORD dwFlags, HANDLE hToken, PWSTR *ppszPath)
        # dwFlags = 0, hToken = None (現在ユーザー)
        hr = _shell32.SHGetKnownFolderPath(ctypes.byref(FOLDERID_Pictures), 0, None, ctypes.byref(ptr))
        if hr == 0 and ptr.value:
            path = Path(ptr.value)
            # CoTaskMemFree で解放
            ctypes.windll.ole32.CoTaskMemFree(ptr)
            return path
    except Exception:
        pass

    # フォールバック
    return Path(os.path.expandvars(r"%USERPROFILE%")) / "Pictures"


def main() -> int:
    # Windowsチェック
    if platform.system() != "Windows":
        print("このスクリプトはWindowsでの実行を想定しています。")
        return 1

    # 依存ライブラリ読込
    try:
        from mss import mss
        from mss import tools as mss_tools
    except Exception as e:
        print("mssの読み込みに失敗しました。uvでインストールしてください: uv add mss")
        print(f"詳細: {e}")
        return 2

    try:
        import pygetwindow as gw
    except Exception as e:
        print("PyGetWindowの読み込みに失敗しました。uvでインストールしてください: uv add PyGetWindow")
        print(f"詳細: {e}")
        return 3

    print("5秒待機後、アクティブウィンドウをキャプチャします…")
    time.sleep(5)

    # アクティブウィンドウ取得
    win = gw.getActiveWindow()
    if win is None:
        print("アクティブウィンドウを取得できませんでした。")
        return 4

    # 必要に応じて前面化
    try:
        if not win.isActive:
            win.activate()
            time.sleep(0.2)
    except Exception:
        # activateが未サポートでも続行
        pass

    # ウィンドウの領域（全体: タイトルバーと枠含む）
    left, top, width, height = win.left, win.top, win.width, win.height
    if any(v is None for v in (left, top, width, height)):
        print("ウィンドウ座標の取得に失敗しました。")
        return 5

    left, top, width, height = int(left), int(top), int(width), int(height)
    if width <= 0 or height <= 0:
        print("ウィンドウサイズが不正です。")
        return 6

    # スクリーンショット取得（mss）
    try:
        with mss() as sct:
            monitor = {"left": left, "top": top, "width": width, "height": height}
            shot = sct.grab(monitor)
    except Exception as e:
        print("スクリーンショットの取得に失敗しました。ウィンドウ位置やマルチモニタ構成を確認してください。")
        print(f"詳細: {e}")
        return 6

    # 保存先
    out_dir = get_pictures_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "capture.png"

    try:
        # mss.tools.to_png で直接保存
        mss_tools.to_png(shot.rgb, shot.size, output=str(out_path))
    except Exception as e:
        print("ファイル保存に失敗しました。権限やパスを確認してください。")
        print(f"詳細: {e}")
        return 7

    print(f"保存しました: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
