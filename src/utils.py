"""共通ユーティリティ関数群。

Python 3.12 対応。型注釈と日本語docstringを付与。
"""

from __future__ import annotations

from datetime import datetime


def timestamp_for_filename(dt: datetime | None = None) -> str:
    """ファイル名用のタイムスタンプ文字列を返す。

    形式は ``YYYYMMDD-HHMMSS`` （例: ``20250830-123408``）。

    Args:
        dt: 任意で日時を指定。未指定なら現在時刻。

    Returns:
        ファイル名に使用できるタイムスタンプ文字列。
    """
    now = dt or datetime.now()
    return now.strftime("%Y%m%d-%H%M%S")


def ensure_suffix(text: str, suffix: str) -> str:
    """文字列が指定サフィックスで終わるようにする。

    Args:
        text: 対象文字列。
        suffix: 付与したいサフィックス。

    Returns:
        必要であればサフィックスを付けた文字列。
    """
    return text if text.endswith(suffix) else f"{text}{suffix}"
