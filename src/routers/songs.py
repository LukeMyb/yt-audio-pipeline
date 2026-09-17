import os
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from mutagen.mp4 import MP4
from src.services.jellyfin import refresh_jellyfin
from src.services.logger import delete_logger

# ルーターの立ち上げ
router = APIRouter()

# 対象ディレクトリの設定
ACTIVE_DIR = os.path.join("data", "active")
TRASH_DIR = os.path.join("data", "trash")

# フロントエンドに返す楽曲データの型定義
class Song(BaseModel):
    filename: str
    title: str
    artist: str

# 楽曲一覧取得API（GET /api/songs）
@router.get("/", response_model=list[Song])
def get_songs():
    songs = []
    target_dir = Path(ACTIVE_DIR)
    
    if not target_dir.exists():
        return songs

    # activeフォルダ内のm4aファイルを検索
    for filepath in target_dir.rglob("*.m4a"):
        try:
            audio = MP4(filepath)
            # m4aのメタデータ（タグ）から曲名とアーティスト名を取得
            # 存在しない場合はファイル名やUnknownを代入
            title = audio.tags.get("\xa9nam", [filepath.stem])[0] if audio.tags else filepath.stem
            artist = audio.tags.get("\xa9ART", ["Unknown Artist"])[0] if audio.tags else "Unknown Artist"
            
            songs.append(Song(
                filename=filepath.name,
                title=title,
                artist=artist
            ))
        except Exception as e:
            print(f"[API] メタデータ読み込みエラー ({filepath.name}): {e}")
            # エラー時も最低限ファイル名だけは返す
            songs.append(Song(
                filename=filepath.name,
                title=filepath.stem,
                artist="Unknown Artist"
            ))
    
    return songs

# 楽曲削除API（DELETE /api/songs/{filename}）
@router.delete("/{filename}")
def delete_song(filename: str):
    # セキュリティ対策: パストラバーサル（../等を使ったディレクトリ移動）を防止
    safe_filename = os.path.basename(filename)
    target_path = Path(ACTIVE_DIR) / safe_filename

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    
    try:
        # 物理削除ではなく、ゴミ箱ディレクトリへの移動（論理削除）
        trash_path = Path(TRASH_DIR) / safe_filename
        shutil.move(str(target_path), str(trash_path))
        
        # Jellyfinのライブラリ更新をトリガー
        jelly_msg = refresh_jellyfin()
        
        msg = f"[API] ファイルをゴミ箱に移動しました: {safe_filename}"
        if jelly_msg:
            msg += f" ({jelly_msg})"
        print(msg)
        delete_logger.info(msg)
        
        return {
            "message": "ゴミ箱へ移動完了",
            "filename": safe_filename,
            "jellyfin_status": jelly_msg
        }
    except Exception as e:
        error_msg = f"削除（移動）に失敗しました: {e}"
        delete_logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# サムネイル画像取得API（GET /api/songs/{filename}/thumbnail）
from fastapi.responses import Response

@router.get("/{filename}/thumbnail")
def get_thumbnail(filename: str):
    safe_filename = os.path.basename(filename)
    target_path = Path(ACTIVE_DIR) / safe_filename

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    
    try:
        audio = MP4(target_path)
        covr = audio.tags.get("covr") if audio.tags else None
        
        if covr and len(covr) > 0:
            cover_data = covr[0]
            # マジックバイトで画像形式を簡易判定
            if cover_data.startswith(b'\x89PNG'):
                media_type = "image/png"
            else:
                media_type = "image/jpeg"
                
            # キャッシュを有効にして無駄なファイル読み込みを減らす
            headers = {"Cache-Control": "public, max-age=86400"}
            return Response(content=bytes(cover_data), media_type=media_type, headers=headers)
            
    except Exception as e:
        print(f"[API] サムネイル抽出エラー ({filename}): {e}")
        
    raise HTTPException(status_code=404, detail="サムネイルが見つかりません")

# 音声ファイル取得（再生・ダウンロード用）API（GET /api/songs/{filename}/download）
from fastapi.responses import FileResponse

@router.get("/{filename}/download")
def download_song(filename: str):
    safe_filename = os.path.basename(filename)
    target_path = Path(ACTIVE_DIR) / safe_filename

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
    # Content-Disposition を指定しないことで、ブラウザでのストリーミングプレビューが可能に
    return FileResponse(path=target_path, media_type="audio/mp4")