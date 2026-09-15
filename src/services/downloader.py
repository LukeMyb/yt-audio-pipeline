import os
import subprocess
import sys
import re
from pathlib import Path
from mutagen.mp4 import MP4

# 保存先のディレクトリ設定
SAVE_DIR = os.path.join("data", "active")
BIN_DIR = "bin"

current_status = ""
active_downloads = 0

def update_status(msg: str):
    global current_status
    current_status = msg
    print(msg)

# バックグラウンドでのダウンロード処理
def download_task(original_url: str):
    global active_downloads
    active_downloads += 1
    update_status(f"[Worker] ダウンロードタスクを準備中...")
    # URLから11桁の動画IDを抽出
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
        "-o", output_template
    ]

    # FirefoxブラウザのCookieを読み込む (Chromium系の強固な暗号化を回避するため)
    command.extend(["--cookies-from-browser", "firefox"])
    
    # YouTubeの新しいJSチャレンジ(EJS)を解決するため、Node.jsを使って自動突破する設定
    command.extend(["--remote-components", "ejs:github"])

    command.append(music_url)

    update_status(f"[Worker] yt-dlpによるダウンロードを開始します...")
    try:
        # 10分(600秒)でタイムアウトする安全装置を追加
        subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True, timeout=600)
        update_status(f"[Worker] ダウンロードとフォルダ振り分けが完了しました。")

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
                update_status(f"[Worker] エラー: 動画ID '{video_id}' を含むファイルが見つかりませんでした。")
        else:
            update_status(f"[Worker] エラー: URLから動画IDを抽出できなかったため検索をスキップします。")

        # 音量（LUFS）とピーク値の解析・ReplayGainメタデータの付与
        if filepath:
            update_status(f"[Worker] 音量とピーク値を解析中... ({filepath})")
            
            ffmpeg_exe = os.path.join(BIN_DIR, "ffmpeg.exe") if os.name == 'nt' else os.path.join(BIN_DIR, "ffmpeg")
            # peak=true を指定してTrue Peakも同時に計測
            ffmpeg_cmd = [
                ffmpeg_exe, "-i", filepath,
                "-af", "ebur128=framelog=verbose:peak=true", "-f", "null", "-"
            ]
            # ffmpegは通常数秒で終わるため、60秒でタイムアウトする安全装置を追加
            ffmpeg_result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            
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
                
                update_status(f"[Worker] ReplayGainタグを埋め込みました (ゲイン: {gain_str}, ピーク: {peak_str})")
                # 少し待ってから完了メッセージに切り替えるなど
            else:
                update_status("[Worker] 音量解析に失敗しました。LUFS値またはピーク値が見つかりません。")
                # 解析失敗時にffmpegの出力を表示する
                print("============================== ffmpeg 出力ログ ==============================")
                print(ffmpeg_result.stderr)
                print("=============================================================================")

    except subprocess.TimeoutExpired:
        update_status("[Worker] エラー: 処理がタイムアウトしました。")
    except subprocess.CalledProcessError as e:
        update_status(f"[Worker] エラーが発生しました:\n{e.stderr}")
    except Exception as e:
        update_status(f"[Worker] 予期せぬエラーが発生しました: {str(e)}")
    finally:
        active_downloads -= 1
        print("=" * 50 + "\n")