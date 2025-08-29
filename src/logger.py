"""ログ設定ユーティリティ。

起動時刻に基づくログファイルを `logs/` 配下に作成し、
以降のログを同一ファイルに追記する。
"""

from __future__ import annotations

import logging
from pathlib import Path

from utils import timestamp_for_filename


def setup_file_logger(base_dir: Path) -> tuple[logging.Logger, Path]:
    """ログ出力を設定し、ロガーとログファイルパスを返す。

    Args:
        base_dir: プロジェクトのルートディレクトリ。

    Returns:
        - ``logging.Logger``: 設定済みロガー。
        - ``Path``: 作成したログファイルのパス。
    """
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    ts = timestamp_for_filename()
    logfile = logs_dir / f"{ts}.log"

    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fh = logging.FileHandler(logfile, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # コンソールにも最低限の情報を出す（デバッグ容易化）
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.debug("ロガー初期化完了: %s", logfile)
    return logger, logfile
