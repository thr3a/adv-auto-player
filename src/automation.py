"""自動操作ループの実装。"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import windows
from capture import capture_window_region
from config import AppConfig
from ocr import OcrParagraph, call_ocr_api, extract_paragraphs, find_matching_paragraph


@dataclass
class WindowInfo:
    """ウィンドウ情報（Windows専用）。"""

    hwnd: int
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


def _resolve_window(title_part: str, logger: logging.Logger) -> WindowInfo:
    """タイトル部分一致でウィンドウを探し、前面化して情報取得。"""
    hwnd = windows.find_window_by_partial_title(title_part)
    if not hwnd:
        raise RuntimeError(f"ウィンドウが見つかりません: '{title_part}'")

    windows.bring_to_foreground(hwnd)
    rect = windows.get_window_rect(hwnd)
    logger.debug("ターゲットウィンドウ rect=%s", rect)

    return WindowInfo(hwnd=hwnd, left=rect.left, top=rect.top, right=rect.right, bottom=rect.bottom)


def _click_in_window_center_of_box(win: WindowInfo, box: tuple[int, int, int, int], logger: logging.Logger) -> None:
    """ウィンドウ画像内座標 ``box`` の中心をスクリーン座標に変換してクリック。"""
    x1, y1, x2, y2 = box
    cx = win.left + int((x1 + x2) / 2)
    cy = win.top + int((y1 + y2) / 2)
    logger.info("クリック: (%d, %d) (box=%s)", cx, cy, box)
    windows.bring_to_foreground(win.hwnd)
    windows.click_screen(cx, cy)


def run_automation(base_dir: Path, config: AppConfig, logger: logging.Logger) -> None:
    """自動操作のメインループ。

    1. 対象ウィンドウを探して前面化
    2. interval 毎にキャプチャ→OCR→ログへ候補出力
    3. steps の現在ターゲットに部分一致したらクリック
    4. すべての steps が終わったら終了
    """
    win = _resolve_window(config.title, logger)

    pending_steps: list[str] = list(config.steps)
    logger.info(
        "開始: title='%s', interval=%s, steps=%s, ocr_api_endpoint='%s', keep_height=%s",
        config.title,
        config.interval,
        pending_steps,
        config.ocr_api_endpoint,
        config.capture_keep_height,
    )

    while pending_steps:
        # 念のため毎回前面化＆位置更新
        try:
            win = _resolve_window(config.title, logger)
        except Exception as e:
            logger.error("ウィンドウ取得に失敗: %s", e)
            raise

        img_path = capture_window_region(
            base_dir,
            win.left,
            win.top,
            win.width,
            win.height,
            keep_height=config.capture_keep_height,
        )
        logger.debug("キャプチャ保存: %s", img_path)

        try:
            data = call_ocr_api(config.ocr_api_endpoint, img_path)
        except Exception as e:
            logger.error("OCR API 失敗: %s", e)
            time.sleep(config.interval)
            continue

        paragraphs: list[OcrParagraph] = extract_paragraphs(data)

        # 候補をログに出す（デバッグ目的）
        if not paragraphs:
            logger.info("OCR words: 0件")
        else:
            logger.info("OCR words (%d件):", len(paragraphs))
            for p in paragraphs:
                logger.info(" - '%s' box=%s", p.text, p.box)

        current = pending_steps[0]
        hit = find_matching_paragraph(current, paragraphs)
        if hit:
            logger.info("一致: step='%s' -> クリック実行", current)
            _click_in_window_center_of_box(win, hit.box, logger)
            pending_steps.pop(0)
        else:
            logger.debug("未一致: step='%s'", current)
        time.sleep(config.interval)

    logger.info("全てのステップが完了しました。終了します。")
