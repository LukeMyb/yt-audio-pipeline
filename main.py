import os
import subprocess
import sys
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import uvicorn

# FastAPIアプリケーションの立ち上げ
app = FastAPI()

# 保存先とツール類のディレクトリ設定
SAVE_DIR = "downloads"
BIN_DIR = "bin"

# downloadsフォルダが存在しない場合は自動作成
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 受け取るデータ（JSON）の形を定義
class URLRequest(BaseModel):
    url: str

# バックグラウンドでのダウンロード処理
def download_task(original_url: str):
    # URL変換
    music_url = original_url.replace("www.youtube.com", "music.youtube.com").replace("youtu.be/", "music.youtube.com/watch?v=")
    # 保存パスのテンプレート作成（アーティスト名/曲名 [ID].m4a）
    output_template = os.path.join(SAVE_DIR, "%(uploader)s", "%(title)s [%(id)s].%(ext)s")

    # yt-dlpコマンドの組み立て
    command = [
        sys.executable, "-m", "yt_dlp",
        "-x",
        "--audio-format", "m4a",
        "--audio-quality", "128K",
        "--add-metadata",
        "--embed-thumbnail",
        "--ffmpeg-location", BIN_DIR,
        # 「音声抽出(ExtractAudio)」の時だけAACでの再エンコードと音量正規化を行う
        "--postprocessor-args", "ExtractAudio:-c:a aac -af loudnorm=I=-14:TP=-1.5:LRA=11",
        "-o", output_template,
        music_url
    ]

    print(f"[Worker] yt-dlpによるダウンロードを開始します...")
    try:
        # 同期実行
        subprocess.run(command, capture_output=True, text=True, check=True)
        print("[Worker] ダウンロードとフォルダ振り分けが完了しました。")
    except subprocess.CalledProcessError as e:
        print(f"[Worker] ダウンロードに失敗しました:\n{e.stderr}")
    
    print("=" * 50 + "\n")

# POST通信の窓口（/add）を作成
@app.post("/add")
def add_to_queue(request: URLRequest, background_tasks: BackgroundTasks):
    # 届いたURLをターミナルに表示する
    print("\n" + "=" * 50)
    print(f"[Endpoint] URLを受信しました: {request.url}")
    
    # download_taskにURLをパス
    background_tasks.add_task(download_task, request.url)
    
    return PlainTextResponse("バックグラウンドでダウンロードを開始しました")

if __name__ == "__main__":
    # host="0.0.0.0" でTailscale経由のアクセスを許可
    uvicorn.run(app, host="100.88.57.78", port=8000)