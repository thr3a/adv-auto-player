- 会話とコード内のコメントは日本語でお願いします。
- Python 3.12.8
- まずはpyproject.tomlを読み込んで使用ライブラリ、コードスタイル(ruffルール)に準拠すること
- 型注釈・docstringを活用すること
- パッケージはuvで管理している。インストールされたパッケージは.venv/以下に入っている

- 開発環境はMacOSだが本番実行はwindowsを想定している。
- cliのオプションパースにはclickを http通信にはrequestsを使う
- 仕様変更後はAGENTS.mdの中身も書き換えること。

# 概要

- 依頼内容に基づき、CLI・設定読み込み・ログ・ウィンドウ操作（Windows）・キャプチャ・OCR・自動クリックを分割実装しました。
- 実行例: uv run python src/main.py --config hoge.yml
    - ymlの実装例は kanogi.yml にある
- ログ: logs/YYYYMMDD-HHMMSS.log（起動ごとに新規作成、以後追記）
- キャプチャ: capture/YYYYMMDD-HHMMSS.png（ターゲットウィンドウを定期保存。任意で上部のみ）
- OCR: 設定ファイルの `ocr_api_endpoint`（例: `http://deep01.local:3200`）に対して、コード側で固定のパス `/analyze?format=json` を付与して画像をPOST。paragraphs候補文字列をログ出力→stepsに部分一致したらクリック
    - APIのレスポンス例は ocr-api-response-example.json にある

- 依存パッケージ: click, requests, mss, PyYAML（pyproject.tomlに追記済み）
- 実装ファイル:
    - src/main.py: CLIエントリ（--config）
    - src/config.py: YAML設定読込（title/interval/steps/ocr_api_endpoint/capture_keep_height）
    - src/logger.py: 起動時刻ベースのログファイル生成
    - src/utils.py: タイムスタンプ生成などのユーティリティ
    - src/windows.py: Windows専用のウィンドウ検索/前面化/座標取得/クリック（ctypes）
    - src/capture.py: mssで領域キャプチャ保存（上部のみ残すオプション対応）
    - src/ocr.py: OCR API呼び出しとparagraphs抽出
    - src/automation.py: 自動操作ループ（キャプチャ→OCR→ログ→クリック）
- JSONパース: example.jsonの構造に合わせ、content[].paragraphs と content[].figures[].paragraphs の両方から候補文字列を抽出し、全件ログに出力します。

# 処理フロー

- `GET {ocr_api_endpoint}/health` を `timeout=10秒` で実行し、`{"status": "ok"}` が取得できた場合のみ続行
- ウィンドウ探索: title 部分一致で最初に見つかった可視ウィンドウを対象化。見つからなければ例外で終了。
- ループ:
    - ウィンドウを前面化し、座標を取得
    - ウィンドウをキャプチャして capture/ に保存（必要に応じて上部のみ）
    - OCR APIに画像POST→JSON取得
    - paragraphs候補文字列をログ出力
    - steps の先頭要素に部分一致する段落があれば、その段落の box=[x1,y1,x2,y2] 中心をスクリーン座標に変換して左クリック
    - 1画像で1クリックのみ（次ステップは次のキャプチャで判定）
    - steps をすべて消化したら終了

# 実装上の注意

- DPI対策: SetProcessDPIAware() を試行（失敗時は継続）。
- 文字一致: 部分一致。比較前に名寄せ（正規化）を実施し、以下を半角化してから比較します。
- クリック座標: キャプチャと同じウィンドウ矩形をオフセットとして用いるため、OCRのboxと整合が取れます。
- 例外処理: 設定読込・ウィンドウ取得・OCR呼び出しで適宜例外をログに記録。OCR失敗時は待機してリトライ。

## 追加仕様（画面下部のノベルテキスト誤クリック対策）

- 設定キー `capture_keep_height`（任意・整数）を追加。
  - 指定時はターゲットウィンドウ上部からそのピクセル数だけをキャプチャ・OCR 対象とする。
  - 例: ウィンドウ高さ 800px、`capture_keep_height: 500` の場合、上部 500px を使用し、下部 300px は無視。
  - 未指定または 1 未満の値の場合は全体を使用。
  - クリック座標はキャプチャ基準の画像内座標をウィンドウ左上にオフセットして算出するため、
    上部のみのキャプチャでも正しい位置をクリックします。
