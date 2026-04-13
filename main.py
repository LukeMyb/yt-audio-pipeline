from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# FastAPIアプリケーションの立ち上げ
app = FastAPI()

# 受け取るデータ（JSON）の形を定義
class URLRequest(BaseModel):
    url: str

# POST通信の窓口（/add）を作成
@app.post("/add")
async def receive_url(request: URLRequest):
    # 届いたURLをPCの画面（ターミナル）に大きく表示する
    print("\n" + "=" * 50)
    print("🎉 【通信成功】 iPhoneから以下のURLを受信しました！")
    print(request.url)
    print("=" * 50 + "\n")
    
    # iPhone側のショートカットに完了の返事をする
    return {"status": "success", "message": "テスト受信完了"}

if __name__ == "__main__":
    # host="0.0.0.0" でTailscale経由のアクセスを許可
    uvicorn.run(app, host="100.88.57.78", port=8000)