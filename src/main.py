"""CLI エントリポイント。

実行例: ``uv run python src/main.py --config hoge.yml``
"""

from __future__ import annotations

from pathlib import Path

import click

from automation import run_automation
from config import AppConfig, load_config
from logger import setup_file_logger
from ocr import check_ocr_health


@click.command()
@click.option("--config", "config_path", type=click.Path(path_type=Path, exists=True, dir_okay=False), required=True, help="設定YAMLファイルのパス")
def main(config_path: Path) -> None:
    """テキストノベルゲームの自動操作アプリを起動する。"""
    base_dir = Path(__file__).resolve().parent.parent
    logger, logfile = setup_file_logger(base_dir)
    logger.info("ログファイル: %s", logfile)

    try:
        config: AppConfig = load_config(config_path)
    except Exception as e:
        logger.exception("設定の読み込みに失敗しました: %s", e)
        raise SystemExit(2) from e

    # OCR サーバーヘルスチェック（/health が {"status": "ok"} を返すか）
    if not check_ocr_health(config.ocr_api_endpoint, timeout=10.0):
        logger.error("OCRサーバーが起動していません: %s", config.ocr_api_endpoint)
        raise SystemExit(3)

    try:
        run_automation(base_dir, config, logger)
    except Exception as e:
        logger.exception("実行中にエラーが発生しました: %s", e)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
