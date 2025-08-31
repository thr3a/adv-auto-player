"""共通ユーティリティ関数群。

型注釈と日本語docstringを付与。
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


def normalize_text_for_matching(text: str) -> str:
    """名寄せのための簡易正規化を行う。

    要件:
    - アルファベットを半角化（例: ａ→a, Ｚ→Z）
    - 数字を半角化（例: １→1）
    - 全角スペースを半角スペースにする（U+3000→U+0020）

    それ以外の記号・日本語の形は保持する（NFKCのような広範囲の互換分解は行わない）。

    Args:
        text: 入力文字列。

    Returns:
        名寄せ用に正規化した文字列。
    """
    # 変換テーブルを動的に構築（範囲ごとに半角へ）
    # 全角スペース U+3000 -> 半角スペース U+0020
    trans: dict[int, int] = {0x3000: 0x20}

    # 全角数字 U+FF10..U+FF19 -> '0'..'9'
    for i in range(0xFF10, 0xFF19 + 1):
        trans[i] = ord('0') + (i - 0xFF10)

    # 全角大文字 U+FF21..U+FF3A -> 'A'..'Z'
    for i in range(0xFF21, 0xFF3A + 1):
        trans[i] = ord('A') + (i - 0xFF21)

    # 全角小文字 U+FF41..U+FF5A -> 'a'..'z'
    for i in range(0xFF41, 0xFF5A + 1):
        trans[i] = ord('a') + (i - 0xFF41)

    return text.translate(trans)
