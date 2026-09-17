from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from src.services.downloader import download_task, current_status
import src.services.downloader as downloader
from src.services.logger import download_logger
from fastapi.responses import StreamingResponse
import asyncio
import json
from fastapi import Request

# ルーターの立ち上げ
router = APIRouter()

# 受け取るデータ（JSON）の形を定義
class URLRequest(BaseModel):
    url: str

# 従来のステータス取得（念のため残す）
@router.get("/status")
def get_status():
    return {
        "status": downloader.current_status,
        "is_active": downloader.active_downloads > 0
    }

# SSE（Server-Sent Events）を用いたリアルタイムストリーミング通信
@router.get("/status/stream")
async def status_stream(request: Request):
    async def event_generator():
        last_status = None
        while True:
            # クライアントが切断されたらループを終了してメモリ解放
            if await request.is_disconnected():
                break
                
            current = downloader.current_status
            is_active = downloader.active_downloads > 0
            
            # ステータスが変化した時だけデータをプッシュ送信
            if current != last_status:
                last_status = current
                data = json.dumps({"status": current, "is_active": is_active})
                yield f"data: {data}\n\n"
            
            # 内部で1秒待機（ネットワーク通信は発生しない）
            await asyncio.sleep(1)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# POST通信の窓口（/add）を作成
@router.post("/add")
def add_to_queue(request: URLRequest, background_tasks: BackgroundTasks):
    # 届いたURLをターミナルに表示する
    msg = f"[Endpoint] URLを受信しました: {request.url}"
    print("\n" + "=" * 50)
    print(msg)
    download_logger.info("=" * 50)
    download_logger.info(msg)
    
    # download_taskにURLをパス
    background_tasks.add_task(download_task, request.url)
    
    return PlainTextResponse("バックグラウンドでダウンロードを開始しました")