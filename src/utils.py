"""共通ユーティリティ関数群。"""

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


def normalize_text_for_matching(text: str) -> str:
    """名寄せのための簡易正規化を行う。"""
    # 変換テーブルを動的に構築（範囲ごとに半角へ）
    # 全角スペース U+3000 -> 半角スペース U+0020
    trans: dict[int, int] = {0x3000: 0x20}

    # 全角数字 U+FF10..U+FF19 -> '0'..'9'
    for i in range(0xFF10, 0xFF19 + 1):
        trans[i] = ord("0") + (i - 0xFF10)

    # 全角大文字 U+FF21..U+FF3A -> 'A'..'Z'
    for i in range(0xFF21, 0xFF3A + 1):
        trans[i] = ord("A") + (i - 0xFF21)

    # 全角小文字 U+FF41..U+FF5A -> 'a'..'z'
    for i in range(0xFF41, 0xFF5A + 1):
        trans[i] = ord("a") + (i - 0xFF41)

    return text.translate(trans)
