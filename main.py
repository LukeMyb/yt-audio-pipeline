import os
import subprocess
import sys
from fastapi import FastAPI
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

# POST通信の窓口（/add）を作成
@app.post("/add")
def add_to_queue(request: URLRequest):
    # 届いたURLをターミナルに表示する
    print("\n" + "=" * 50)
    print(f"[受信] iPhoneからURLを受け取りました: {request.url}")
    
    # URLをYouTube Music仕様に変換
    music_url = request.url.replace("www.youtube.com", "music.youtube.com").replace("youtu.be/", "music.youtube.com/watch?v=")
    print(f"[変換] YouTube Music URL: {music_url}")
    
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
        "-o", output_template,
        music_url
    ]

    print(f"[実行] yt-dlpによるダウンロードを開始します...")
    
    try:
        # subprocess.run で同期実行（終わるまでPC側は待機）
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("[成功] ダウンロードとフォルダ振り分けが完了しました！")
        print("=" * 50 + "\n")
        return {"status": "success", "message": "保存が完了しました"}
    
    except subprocess.CalledProcessError as e:
        print(f"[エラー] ダウンロードに失敗しました:\n{e.stderr}")
        print("=" * 50 + "\n")
        return {"status": "error", "message": "ダウンロード失敗"}

if __name__ == "__main__":
    # host="0.0.0.0" でTailscale経由のアクセスを許可
    uvicorn.run(app, host="100.88.57.78", port=8000)