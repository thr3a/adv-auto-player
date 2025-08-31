"""ウィンドウ領域のキャプチャ保存。"""

from __future__ import annotations

from pathlib import Path

from mss import mss, tools

from utils import timestamp_for_filename


def capture_window_region(
    base_dir: Path,
    left: int,
    top: int,
    width: int,
    height: int,
    *,
    keep_height: int | None = None,
) -> Path:
    """指定領域をキャプチャして ``capture/`` にPNG保存する。

    Args:
        base_dir: プロジェクトルート。
        left: スクリーン座標の左上X。
        top: スクリーン座標の左上Y。
        width: 幅。
        height: 高さ。
        keep_height: 任意。上部からこのピクセル数だけを残して保存する。
            未指定または 1 未満の場合は全体を保存。

    Returns:
        保存した画像のパス。
    """
    cap_dir = base_dir / "capture"
    cap_dir.mkdir(parents=True, exist_ok=True)

    ts = timestamp_for_filename()
    out_path = cap_dir / f"{ts}.png"

    # 高さの制限（上部のみ使用）
    effective_height = int(height)
    if keep_height is not None and keep_height > 0:
        effective_height = max(1, min(int(height), int(keep_height)))

    region = {
        "left": int(left),
        "top": int(top),
        "width": int(width),
        "height": effective_height,
    }
    with mss() as sct:
        img = sct.grab(region)
        png_bytes = tools.to_png(img.rgb, img.size)
        out_path.write_bytes(png_bytes)

    return out_path
