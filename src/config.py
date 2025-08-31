"""YAML 設定ファイルの読み込みとスキーマ定義。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class AppConfig:
    """アプリ設定。

    Attributes:
        title: 部分一致で探す対象ウィンドウのタイトル。
        interval: キャプチャ間隔（秒）。デフォルト5秒。
        steps: クリック対象となる文字列の配列（順番に処理）。
        ocr_api_endpoint: OCR API のベースエンドポイント（例: ``http://deep01.local:3200``）。
    """

    title: str
    interval: int
    steps: list[str]
    ocr_api_endpoint: str


def load_config(path: Path) -> AppConfig:
    """設定ファイルを読み込み、``AppConfig`` を返す。

    Args:
        path: YAML設定ファイルのパス。

    Returns:
        パース済み ``AppConfig``。
    """
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    title = str(data.get("title", "")).strip()
    if not title:
        raise ValueError("設定 'title' が未指定です")

    interval = int(data.get("interval", 5))
    steps_raw = data.get("steps", []) or []
    if not isinstance(steps_raw, list):
        raise ValueError("設定 'steps' は配列である必要があります")
    steps = [str(s) for s in steps_raw]

    # OCR API のベースエンドポイントは必須（デフォルト無し）
    endpoint_raw = data.get("ocr_api_endpoint")
    if endpoint_raw is None:
        raise ValueError("設定 'ocr_api_endpoint' が未指定です（必須）")
    endpoint = str(endpoint_raw).strip()
    if not endpoint:
        raise ValueError("設定 'ocr_api_endpoint' が空文字です（必須）")

    return AppConfig(title=title, interval=interval, steps=steps, ocr_api_endpoint=endpoint)
