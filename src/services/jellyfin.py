import os
import urllib.request
import urllib.error

def refresh_jellyfin():
    """
    環境変数に設定されたJellyfinのURLとAPIキーを使用して、
    ライブラリの更新(スキャン)を強制的にトリガーします。
    """
    url = os.getenv("JELLYFIN_URL")
    api_key = os.getenv("JELLYFIN_API_KEY")

    if not url or not api_key:
        return None

    endpoint = f"{url.rstrip('/')}/Library/Refresh"
    
    try:
        req = urllib.request.Request(endpoint, method="POST")
        req.add_header("X-Emby-Token", api_key)
        req.add_header("Content-Length", "0") # POSTのボディが空であることを明示
        
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status in (200, 204):
                msg = "[Jellyfin] ライブラリの更新をリクエストしました"
                print(msg)
                return msg
            else:
                msg = f"[Jellyfin] 更新リクエスト失敗: HTTP {response.status}"
                print(msg)
                return msg
    except Exception as e:
        msg = f"[Jellyfin] API呼び出しエラー: {e}"
        print(msg)
        return msg
