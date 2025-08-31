"""OCR API クライアントおよび結果パース。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


def _as_box(points_or_box: Any) -> tuple[int, int, int, int] | None:
    """``points`` もしくは ``box`` を汎用的に [x1,y1,x2,y2] へ変換する。

    - ``box``: [x1,y1,x2,y2] を期待。長さ<4 は None。
    - ``points``: [[x,y], [x,y], [x,y], [x,y]] を期待。min/max で外接矩形を生成。
    """
    if not points_or_box:
        return None

    # 既に box 形式
    if isinstance(points_or_box, (list, tuple)) and len(points_or_box) >= 4 and all(isinstance(v, (int, float)) for v in points_or_box[:4]):
        x1, y1, x2, y2 = points_or_box[:4]
        return int(x1), int(y1), int(x2), int(y2)

    # points 形式（四角形の各頂点など）
    try:
        pts = list(points_or_box)
        if not pts:
            return None
        xs: list[int] = []
        ys: list[int] = []
        for pt in pts:
            # pt は [x, y] もしくは (x, y) を想定
            if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                xs.append(int(pt[0]))
                ys.append(int(pt[1]))
        if not xs or not ys:
            return None
        return min(xs), min(ys), max(xs), max(ys)
    except Exception:
        return None


def extract_paragraphs(data: dict) -> list[OcrParagraph]:
    """APIレスポンスから words を抽出して正規化する。

    以前は paragraphs と figures[].paragraphs を参照していたが、
    認識精度の観点から words のみを候補集合とする。
    """
    out: list[OcrParagraph] = []

    contents = data.get("content") or []
    for page in contents:
        # words のみを対象にする
        for w in page.get("words", []) or []:
            text = str(w.get("content") or w.get("contents") or "")
            box_raw: Any = w.get("box") or w.get("points")
            box = _as_box(box_raw)
            if not text or not box:
                continue
            out.append(OcrParagraph(text=text, box=box))

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
