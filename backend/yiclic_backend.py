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
    shop_scores_sorted_records = result.get("shop_scores_sorted_records") or []
    all_reviews = result.get("all_reviews")

    # 建立 name -> place_id 映射，供前端聚焦地圖用
    name_to_place_id = {}
    for shop in target_shops:
        name = shop.get("name") or ""
        place_id = shop.get("place_id")
        if name and place_id:
            name_to_place_id[name] = place_id

    print(">> pipeline done, preparing response")
    top_sorted = []
    for row in shop_scores_sorted_records:
        entry = {}
        for k, v in row.items():
            if hasattr(v, "item"):
                v = v.item()
            if v != v:
                v = None
            entry[k] = v
        name = entry.get("shop") or entry.get("name") or ""
        top_sorted.append({
            "name": name,
            "place_id": name_to_place_id.get(name),
            "dirT_score": entry.get("dirT_score"),
        })

    print("<< response ready"+str(len(all_reviews))+" reviews, "+str(len(top_sorted))+" shops sorted")

    return {
        "all_reviews": all_reviews,
        "top_sorted": top_sorted,
    }
