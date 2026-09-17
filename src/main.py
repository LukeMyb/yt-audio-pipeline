import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from src.routers import download
from src.routers import songs
from src.routers import logs

load_dotenv()

# FastAPIアプリケーションの立ち上げ
app = FastAPI()

# CORSの設定（すべてのオリジンからの通信を許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(download.router)
app.include_router(songs.router, prefix="/api/songs")
app.include_router(logs.router, prefix="/api/logs")

# 保存先のディレクトリ設定
ACTIVE_DIR = os.path.join("data", "active")
TRASH_DIR = os.path.join("data", "trash")

# downloadsフォルダが存在しない場合は自動作成
os.makedirs(ACTIVE_DIR, exist_ok=True)
os.makedirs(TRASH_DIR, exist_ok=True)

if __name__ == "__main__":
    # 環境変数から取得（設定がない場合のデフォルト値も設定）
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8749))
    
    uvicorn.run(app, host=host, port=port)