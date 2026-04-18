import os
import subprocess
import sys
import re
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import uvicorn
from mutagen.mp4 import MP4

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
    # ★追加: URLから11桁の動画IDを抽出
    video_id = None
    id_match = re.search(r"(?:v=|\.be\/)([a-zA-Z0-9_-]{11})", original_url)
    if id_match:
        video_id = id_match.group(1)

    # URL変換
    music_url = original_url.replace("www.youtube.com", "music.youtube.com").replace("youtu.be/", "music.youtube.com/watch?v=")
    # 保存パスのテンプレート作成（アーティスト名/曲名 [ID].m4a）
    output_template = os.path.join(SAVE_DIR, "%(title)s [%(id)s].%(ext)s")

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

    print(f"[Worker] yt-dlpによるダウンロードを開始します...")
    try:
        subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
        print(f"[Worker] ダウンロードとフォルダ振り分けが完了しました。")

        # ダウンロード完了後のファイル検索プロセス
        filepath = None
        if video_id:
            target_dir = Path(SAVE_DIR)
            all_m4a_files = list(target_dir.rglob("*.m4a"))
            target_filename_part = f"[{video_id}]"
            found_files = [f for f in all_m4a_files if target_filename_part in f.name]
            
            if found_files:
                filepath = str(found_files[0])
            else:
                print(f"[Worker] エラー: 動画ID '{video_id}' を含むファイルが見つかりませんでした。")
        else:
            print(f"[Worker] エラー: URLから動画IDを抽出できなかったため検索をスキップします。")

        # 音量（LUFS）とピーク値の解析・ReplayGainメタデータの付与
        if filepath:
            print(f"[Worker] 音量とピーク値を解析中... ({filepath})")
            
            ffmpeg_exe = os.path.join(BIN_DIR, "ffmpeg.exe") if os.name == 'nt' else os.path.join(BIN_DIR, "ffmpeg")
            # peak=true を指定してTrue Peakも同時に計測
            ffmpeg_cmd = [
                ffmpeg_exe, "-i", filepath,
                "-af", "ebur128=framelog=verbose:peak=true", "-f", "null", "-"
            ]
            ffmpeg_result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            
            # LUFSとTrue Peak（dBFS）の抽出
            lufs_match = re.search(r"I:\s+([-\d\.]+)\s+LUFS", ffmpeg_result.stderr)
            peak_match = re.search(r"Peak:\s+([-\d\.]+)\s+dBFS", ffmpeg_result.stderr)

            if lufs_match and peak_match:
                integrated_lufs = float(lufs_match.group(1))
                true_peak_dbfs = float(peak_match.group(1))
                
                # ゲインの計算（目標 -14.0 LUFS）
                target_lufs = -14.0
                gain_db = target_lufs - integrated_lufs
                
                # ReplayGain用にフォーマット（dBFSから振幅の比率に変換）
                gain_str = f"{gain_db:+.2f} dB"
                peak_linear = 10 ** (true_peak_dbfs / 20)
                peak_str = f"{peak_linear:.6f}"
                
                # m4aにカスタムタグとして書き込み
                audio = MP4(filepath)
                audio["----:com.apple.iTunes:REPLAYGAIN_TRACK_GAIN"] = [gain_str.encode('utf-8')]
                audio["----:com.apple.iTunes:REPLAYGAIN_TRACK_PEAK"] = [peak_str.encode('utf-8')]
                audio.save()
                
                print(f"[Worker] ReplayGainタグを埋め込みました (ゲイン: {gain_str}, ピーク: {peak_str})")
            else:
                print("[Worker] 音量解析に失敗しました。LUFS値またはピーク値が見つかりません。")
                # 解析失敗時にffmpegの出力を表示する
                print("============================== ffmpeg 出力ログ ==============================")
                print(ffmpeg_result.stderr)
                print("=============================================================================")

    except subprocess.CalledProcessError as e:
        print(f"[Worker] エラーが発生しました:\n{e.stderr}")
    
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