import os
from fastapi import APIRouter, HTTPException

router = APIRouter()
LOGS_DIR = os.path.join("data", "logs")

@router.get("/{log_type}")
def get_log(log_type: str):
    if log_type not in ["download", "delete"]:
        raise HTTPException(status_code=400, detail="Invalid log type")
        
    log_path = os.path.join(LOGS_DIR, f"{log_type}.log")
    
    if not os.path.exists(log_path):
        return {"content": "ログファイルがありません。"}
        
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ログファイルの読み込みに失敗しました: {e}")
