import os
import logging
from logging.handlers import RotatingFileHandler

# ログディレクトリの作成
LOG_DIR = os.path.join("data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name: str, log_file: str, level=logging.INFO):
    """
    指定された名前とファイル名でロガーをセットアップします。
    ファイルサイズが大きくなったら自動でローテーション（バックアップ）されます。
    """
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    file_path = os.path.join(LOG_DIR, log_file)
    # 最大5MB、バックアップは3世代まで保持
    handler = RotatingFileHandler(file_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # ハンドラーが重複して追加されないようにする
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

# 各機能用のロガーを初期化
download_logger = setup_logger('download_logger', 'download.log')
delete_logger = setup_logger('delete_logger', 'delete.log')
