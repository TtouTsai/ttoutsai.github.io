from pathlib import Path

try:
    from .yiclic import run_pipeline, SERPAPI_API_KEY
except ImportError:
    from yiclic import run_pipeline, SERPAPI_API_KEY


def pipeline_for_shops(
    target_shops,
    api_key: str | None = None,
    max_reviews_per_shop: int = 5,
    max_pages_per_shop: int = 3,
):
    """
    給 API 使用的封裝：接受前端送來的 place_id/name 陣列，執行整個 pipeline，回傳排序結果。
    """
    key = api_key or SERPAPI_API_KEY
    if not key:
        raise RuntimeError("SERPAPI_API_KEY 未設定")

    result = run_pipeline(
        target_shops=target_shops,
        api_key=key,
        max_reviews_per_shop=max_reviews_per_shop,
        max_pages_per_shop=max_pages_per_shop,
    )

    # 只回前端需要的部分：排序好的結果與原始評論
    shop_scores_sorted = result.get("shop_scores_sorted")
    all_reviews = result.get("all_reviews")

    top_sorted = []
    if shop_scores_sorted is not None:
        # 轉成 JSON 可序列化的原生型別
        top_sorted = shop_scores_sorted.to_dict(orient="records")
        top_sorted = [
            {k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()}
            for row in top_sorted
        ]

    return {
        "all_reviews": all_reviews,
        "top_sorted": top_sorted,
    }
