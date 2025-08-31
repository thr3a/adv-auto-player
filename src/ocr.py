"""OCR API クライアントおよび結果パース。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import requests

from utils import normalize_text_for_matching


@dataclass(frozen=True)
class OcrParagraph:
    """OCRで検出された段落候補。"""

    text: str
    box: tuple[int, int, int, int]  # x1, y1, x2, y2（画像内座標）


def _normalize_base(endpoint: str) -> str:
    """末尾スラッシュの有無を吸収したベースURLを返す。"""
    return endpoint.rstrip("/")


def call_ocr_api(base_endpoint: str, image_path: Path, timeout: float = 30.0) -> dict:
    """OCR API を呼び出し、JSONを辞書で返す。

    ベースエンドポイントに対して ``/analyze?format=json`` を付与してPOSTします。

    Args:
        base_endpoint: 例 ``http://deep01.local:3200``（末尾スラッシュ有無はどちらでも可）。
        image_path: 送信する画像のパス。
        timeout: タイムアウト秒。

    Returns:
        JSON辞書。
    """
    url = f"{_normalize_base(base_endpoint)}/analyze?format=json"
    with image_path.open("rb") as f:
        files = {"file": (image_path.name, f, "image/png")}
        resp = requests.post(url, files=files, timeout=timeout)
        resp.raise_for_status()
        return resp.json()


def check_ocr_health(base_endpoint: str, timeout: float = 10.0) -> bool:
    """ヘルスチェック: ``{base}/health`` が ``{"status": "ok"}`` を返すか判定。

    ネットワーク例外やJSON不正、ステータス不一致はいずれも False を返す。
    """
    url = f"{_normalize_base(base_endpoint)}/health"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return False
    return isinstance(data, dict) and data.get("status") == "ok"


def extract_paragraphs(data: dict) -> list[OcrParagraph]:
    """APIレスポンスから paragraphs を抽出して正規化。"""
    out: list[OcrParagraph] = []

    contents = data.get("content") or []
    for page in contents:
        # top-level paragraphs
        for p in page.get("paragraphs", []) or []:
            text = str(p.get("contents") or p.get("content") or "")
            box = p.get("box") or p.get("points")
            if not text or not box or len(box) < 4:
                continue
            out.append(OcrParagraph(text=text, box=tuple(map(int, box[:4]))))

        # figures[].paragraphs
        for fig in page.get("figures", []) or []:
            for p in fig.get("paragraphs", []) or []:
                text = str(p.get("contents") or p.get("content") or "")
                box = p.get("box") or p.get("points")
                if not text or not box or len(box) < 4:
                    continue
                out.append(OcrParagraph(text=text, box=tuple(map(int, box[:4]))))

    return out


def find_matching_paragraph(step_text: str, paragraphs: Sequence[OcrParagraph]) -> OcrParagraph | None:
    """部分一致で ``step_text`` にマッチする段落を探す。

    照合前に双方の文字列へ名寄せ用の正規化を適用し、
    - アルファベットの半角化
    - 数字の半角化
    - 全角スペースを半角スペース
    を行った上で ``in`` 判定を行う。
    """
    target = normalize_text_for_matching(step_text)
    for p in paragraphs:
        candidate = normalize_text_for_matching(p.text)
        if target in candidate:
            return p
    return None
