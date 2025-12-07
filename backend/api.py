import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# 確保可以匯入同層模組（無論是否以套件形式啟動）
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

try:
    from .yiclic_backend import (
        pipeline_for_shops,
        SERPAPI_API_KEY,
    )
except ImportError:
    from yiclic_backend import (
        pipeline_for_shops,
        SERPAPI_API_KEY,
    )


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發階段先允許所有來源，正式環境請鎖定 domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Shop(BaseModel):
    name: str | None = None
    place_id: str


class PlaceRequest(BaseModel):
    target_shops: List[Shop]


@app.post("/api/process_places")
def process_places(data: PlaceRequest):
    if not SERPAPI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="後端未設定 SERPAPI_API_KEY 環境變數，請在啟動前設定。",
        )

    try:
        result = pipeline_for_shops(
            target_shops=[shop.dict() for shop in data.target_shops],
            api_key=SERPAPI_API_KEY,
            max_reviews_per_shop=5,
            max_pages_per_shop=3,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"處理失敗: {exc}")

    top5 = result["top_sorted"][:5]
    return {"top5": top5, "reviews": result["all_reviews"]}
