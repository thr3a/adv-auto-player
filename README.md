PyAutoGui
PyGetWindowのライブラリを使ってwindowsのウィンドウ操作を行いたい

5秒待機して、カレントウィンドウ（アクティブ）なウィンドウのスクリーンショットを取得して
マイピクチャにcapture.pngで保存したい
debug2.pyに実装して

テキストノベルゲームの自動操作アプリを作成したい。
実行はuv run python src/main.py --config hoge.yml
実装はsrc/以下に追加開発しやすいようにファイルを分けつつ作成。
ログは起動時の時間でlogs/20250830-123408.logの形式で(2025年8月30日12:34:8秒の意味)
以後は挙動はそのログファイルに追記していく。1起動1ログファイル ログはデバックしやすいように適宜出力すること

設定ファイルのYAMLには

```yaml
title: 彼女たちの流儀
interval: 5
steps:
  - 大声で驚かす
  - アイスクリーム
  - パリ
```

のようになっている。
まずtitleの文字を含むウィンドウを部分一致で探してそのウィンドウをカレントウィンドウ/先頭に持っている。以下ターゲットウィンドウ
なければ例外はいて終了。
ターゲットウィンドウの画面をyamlのintervalの間隔(秒)だけキャプチャする。デフォルト5秒
キャプチャした画像はこのプロジェクトのcapture以下に20250830-123408.pngの形式で保存していく。ディレクトリなければ作成して
保存した画像をAPI使ってOCRする。シェルスクリプトだと以下のようにすると結果がJSONで得られる。

```
curl -XPOST -F "file=@capture.png" "http://deep01.local:3200/analyze?format=json" | jq . 
```

jsonのサンプルはexample.jsonに保存したので参照してください。
使うのはparagraphsのデータ。paragraphsの候補の文字列をログファイルに書くこと（OCR結果を知りたいため）
"description": "Bounding box of the paragraph in the format [x1, y1, x2, y2]",
stepsにかかれている文字があればターゲットウィンドウ(念の為ここでもアクティブウィンドウにしておく)のその文字の中心を左クリックする。
例の場合だと「大声で驚かす」発見したのでクリック→「アイスクリーム」の文字が見つかったのでクリック→「パリ」の文字が見つかったのでクリック
stepsの文字は部分一致　例えばOCRでは「大声で驚かす！」かもしれないけどマッチさせる
1画像で2回以上のクリックは想定しない。例えば同じ画面に「大声で驚かす」と「アイスクリーム」が同時に出るかもしれないけど最初のstepsの「大声で驚かす」だけ使う
stepsの数だけクリックイベントが発生する。全て終えたらプログラム終了。

```
codex
概要

- 依頼内容に基づき、CLI・設定読み込み・ログ・ウィンドウ操作（Windows）・キャプチャ・OCR・自動クリックを分割実装しました。
- 実行例: uv run python src/main.py --config hoge.yml
- ログ: logs/YYYYMMDD-HHMMSS.log（起動ごとに新規作成、以後追記）
- キャプチャ: capture/YYYYMMDD-HHMMSS.png（ターゲットウィンドウ全体を定期保存）
- OCR: http://deep01.local:3200/analyze?format=json に画像を送信、paragraphs候補文字列をログ出力→stepsに部分一致したらクリック

追加・変更点

- 依存パッケージ: click, requests, mss, PyYAML（pyproject.tomlに追記済み）
- 実装ファイル:
    - src/main.py: CLIエントリ（--config）
    - src/config.py: YAML設定読込（title/interval/steps）
    - src/logger.py: 起動時刻ベースのログファイル生成
    - src/utils.py: タイムスタンプ生成などのユーティリティ
    - src/windows.py: Windows専用のウィンドウ検索/前面化/座標取得/クリック（ctypes）
    - src/capture.py: mssで領域キャプチャ保存
    - src/ocr.py: OCR API呼び出しとparagraphs抽出
    - src/automation.py: 自動操作ループ（キャプチャ→OCR→ログ→クリック）
- JSONパース: example.jsonの構造に合わせ、content[].paragraphs と content[].figures[].paragraphs の両方から候補文字列を抽出し、全件ログに出力します。

処理フロー

- ウィンドウ探索: title 部分一致で最初に見つかった可視ウィンドウを対象化。見つからなければ例外で終了。
- ループ:
    - ウィンドウを前面化し、座標を取得
    - ウィンドウ全体をキャプチャして capture/ に保存
    - OCR APIに画像POST→JSON取得
    - paragraphs候補文字列をログ出力
    - steps の先頭要素に部分一致する段落があれば、その段落の box=[x1,y1,x2,y2] 中心をスクリーン座標に変換して左クリック
    - 1画像で1クリックのみ（次ステップは次のキャプチャで判定）
    - steps をすべて消化したら終了

実装上の注意

- Windows専用コードは src/windows.py に隔離し、使用時のみ遅延import（macOS開発環境でもimport時に落ちないよう配慮）。
- DPI対策: SetProcessDPIAware() を試行（失敗時は継続）。
- 文字一致: 単純な部分一致（例: 「大声で驚かす」 ⊂ 「大声で驚かす！」も一致）。
- クリック座標: キャプチャと同じウィンドウ矩形をオフセットとして用いるため、OCRのboxと整合が取れます。
- 例外処理: 設定読込・ウィンドウ取得・OCR呼び出しで適宜例外をログに記録。OCR失敗時は待機してリトライ。

使い方

- 設定ファイル例:
    - hoge.yml:
    - `title`: ウィンドウタイトルの部分文字列
    - `interval`: キャプチャ間隔（秒、デフォルト5）
    - `steps`: クリックしたい文字列を順番に列挙
- 実行:
    - uv run python src/main.py --config hoge.yml
    - 本番は Windows で実行してください（macOSではウィンドウ操作部は動作しません）。

補足

- ruffルール: pyproject.toml にruff設定は見当たりませんでした。一般的なPEP8/型注釈/Docstringに準拠して実装しています（未使用import等は避けています）。
- 追加の正規化（全角・半角・句読点の揺れ統一）が必要であれば、簡易ノーマライズ（例: Unicode正規化や記号除去）を組み込み可能です。

次の対応案
```
