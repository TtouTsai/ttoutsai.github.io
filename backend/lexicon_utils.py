# lexicon_utils.py
import os
import re
import numpy as np
import pandas as pd
import jieba.posseg as pseg

TEXT_COL  = "snippet"
NOUN_TAGS = {"n", "nr", "ns", "nt", "nz"}
ADJ_TAGS  = {"a", "ad", "an"}


def load_word2logodds(out_dir: str = "./outputs", filename: str = "lexicon_df.parquet"):
    """
    從訓練時存好的 parquet 載入 lexicon_df，建立詞 → log_odds_food 的 dict。
    """
    path = os.path.join(out_dir, filename)
    lexicon_df = pd.read_parquet(path)
    # lexicon_df = pd.read_parquet(path, engine="fastparquet")

    word2logodds = dict(zip(lexicon_df["token"], lexicon_df["log_odds_food"]))
    print(f"[info] WORD2LOGODDS loaded from {path}, size = {len(word2logodds)}")
    return word2logodds
# Re-implementing the robust logic from your commented code:
# def load_word2logodds(out_dir: str = "./outputs", filename: str = "lexicon_df.parquet"):
#     path = os.path.join(out_dir, filename)

#     # 嘗試用不同的 engine 讀取 Parquet
#     for engine in ["pyarrow", "fastparquet"]:
#         try:
#             lexicon_df = pd.read_parquet(path, engine=engine)
#             print(f"[info] load parquet ({engine}): {path}")
#             break
#         except Exception as e:
#             print(f"[warn] parquet {engine} 讀取失敗:", e)
#     else:
#         # 讀取 Parquet 失敗 → CSV fallback
#         csv_path = os.path.splitext(path)[0] + ".csv"
#         print(f"[info] 改讀 CSV: {csv_path}")
#         lexicon_df = pd.read_csv(csv_path)

#     word2logodds = dict(zip(lexicon_df["token"], lexicon_df["log_odds_food"]))
#     print(f"[info] WORD2LOGODDS loaded from {path}, size = {len(word2logodds)}")
#     return word2logodds

def clean_text(s: str) -> str:
    """
    簡單清洗文字：strip + 把多個空白縮成一個。
    """
    if not isinstance(s, str):
        s = str(s)
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def cut_with_pos(text: str):
    """
    jieba.posseg 斷詞 + 詞性標註，回傳 [(詞, 詞性), ...]
    """
    return [(w, t) for w, t in pseg.cut(str(text))]


def compute_lexicon_features(text: str, word2logodds: dict):
    """
    給一段文字 + WORD2LOGODDS，回傳 5 維 lexicon 特徵：
    [noun_count, adj_count, max_logodds, sum_logodds, mean_logodds]
    """
    tokens = cut_with_pos(text)
    noun_count = 0
    adj_count = 0
    logodds_list = []

    for w, t in tokens:
        w = str(w).strip()
        if not w:
            continue
        if w in word2logodds:
            logodds_list.append(word2logodds[w])
            if t in NOUN_TAGS:
                noun_count += 1
            elif t in ADJ_TAGS:
                adj_count += 2  # 形容詞權重 2

    if logodds_list:
        max_logodds = float(np.max(logodds_list))
        sum_logodds = float(np.sum(logodds_list))
        mean_logodds = float(np.mean(logodds_list))
    else:
        max_logodds = 0.0
        sum_logodds = 0.0
        mean_logodds = 0.0

    return [noun_count, adj_count, max_logodds, sum_logodds, mean_logodds]


def add_lex_feats_to_df(df: pd.DataFrame, word2logodds: dict, text_col: str = TEXT_COL):
    """
    幫整個 DataFrame 新增一欄 'lex_feats'（list[5]），方便後續 inference 用。
    """
    df = df.copy()
    df[text_col] = df[text_col].map(clean_text)
    df["lex_feats"] = df[text_col].map(lambda s: compute_lexicon_features(s, word2logodds))
    return df
