# adv-auto-player

テキストノベルゲームの自動操作ツール

## 前提条件

- OS: Windows
- Python: 3.12
- パッケージマネージャ: [uv](https://github.com/astral-sh/uv)
- OCR サーバー: `GET {ocr_api_endpoint}/health -> {"status":"ok"}` を返すこと

## インストール

```bash
uv sync
```

## 使い方

1) 設定ファイル（YAML）を用意します。サンプル: `kanogi.yml`

```yaml
title: 彼女たちの流儀
ocr_api_endpoint: http://deep01.local:3200
interval: 10
steps:
  - 幕開けをとばす
  - 耐える
  - 図書館に行ってみる
  # ...（以降省略）
```

設定キーの説明は「設定ファイル」を参照してください。

2) OCR サーバーを起動し、`GET {ocr_api_endpoint}/health` が `{"status":"ok"}` を返すことを確認します。

3) CLI を実行します。

```bash
uv run python src/main.py --config kanogi.yml
```

## 設定ファイル

- `title`: 部分一致で探す対象ウィンドウのタイトル（必須）。
- `interval`: キャプチャ＋判定の間隔（秒、デフォルト 5）。
- `steps`: クリック対象となる文字列の配列（順番に処理、部分一致）。
- `ocr_api_endpoint`: OCR API のベースURL（例: `http://deep01.local:3200`）。実呼び出しは `POST {base}/analyze?format=json`。
