from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

# 分離したダウンローダーの処理を読み込む
from src.services.downloader import download_task, current_status
import src.services.downloader as downloader

# ルーターの立ち上げ
router = APIRouter()

# 受け取るデータ（JSON）の形を定義
class URLRequest(BaseModel):
    url: str

# ステータス取得の窓口（/status）を作成
@router.get("/status")
def get_status():
    return {
        "status": downloader.current_status,
        "is_active": downloader.active_downloads > 0
    }

# POST通信の窓口（/add）を作成
@router.post("/add")
def add_to_queue(request: URLRequest, background_tasks: BackgroundTasks):
    # 届いたURLをターミナルに表示する
    print("\n" + "=" * 50)
    print(f"[Endpoint] URLを受信しました: {request.url}")
    
    # download_taskにURLをパス
    background_tasks.add_task(download_task, request.url)
    
    return PlainTextResponse("バックグラウンドでダウンロードを開始しました")