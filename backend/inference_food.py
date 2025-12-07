# inference_food.py
import os
import numpy as np
import pandas as pd
import torch
from scipy.special import softmax
from transformers import AutoTokenizer, AutoConfig

from lexbert_model import LexiconEnhancedBertForSequenceClassification
from lexicon_utils import (
    TEXT_COL,
    load_word2logodds,
    add_lex_feats_to_df,
)


def load_lexicon_bert(model_dir: str, device: torch.device | None = None):
    """
    載入訓練好的 Lexicon-Enhanced BERT 模型與 tokenizer。
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    config = AutoConfig.from_pretrained(model_dir)

    model = LexiconEnhancedBertForSequenceClassification.from_pretrained(
        model_dir,
        config=config,
        lex_feat_dim=5,
    )
    model.to(device)
    model.eval()

    print("[info] Lexicon Enhanced 模型載入成功！device =", device)
    return tokenizer, model, device


def predict_proba_food_for_texts(
    texts: list[str],
    tokenizer,
    model,
    word2logodds: dict,
    device: torch.device,
    max_length: int = 128,
    batch_size: int = 32,
):
    """
    對一批文字預測「是食物評論的機率」，回傳 numpy array shape = (N, 2) (每列是 [p_notfood, p_food])
    """
    from lexicon_utils import compute_lexicon_features, clean_text

    # 先清洗＋算 lex_feats
    cleaned = [clean_text(t) for t in texts]
    lex_feats = [compute_lexicon_features(t, word2logodds) for t in cleaned]

    all_probs = []

    model.eval()
    with torch.no_grad():
        for i in range(0, len(cleaned), batch_size):
            batch_texts = cleaned[i:i+batch_size]
            batch_lex = lex_feats[i:i+batch_size]

            enc = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
            enc = {k: v.to(device) for k, v in enc.items()}

            lex_tensor = torch.tensor(batch_lex, dtype=torch.float, device=device)
            outputs = model(**enc, lex_feats=lex_tensor)
            logits = outputs["logits"].cpu().numpy()
            probs = softmax(logits, axis=-1)
            all_probs.append(probs)

    all_probs = np.vstack(all_probs)
    return all_probs  # shape (N, num_labels)


def predict_food_on_csv(
    input_csv: str,
    output_csv: str,
    model_dir: str,
    out_dir_lexicon: str = "./outputs",
    encoding: str = "utf-8-sig",
    threshold: float = 0.5,
    filtered_output_csv: str | None = None,
):
    """
    整條 pipeline：
    1. 從 CSV 載入資料
    2. 載入 WORD2LOGODDS
    3. 算 lex_feats
    4. 載入 Lexicon-BERT
    5. 預測 proba_food，存回 CSV（含機率與預測標籤）
    6. （可選）再輸出一份只保留「預測為食物評論」的檔案
    """
    # 讀資料
    df = pd.read_csv(input_csv, encoding=encoding)
    if TEXT_COL not in df.columns:
        raise ValueError(f"input_csv 缺少文字欄位：{TEXT_COL}")

    # 載入 lexicon dict
    word2logodds = load_word2logodds(out_dir=out_dir_lexicon)

    # 加上 lex_feats 欄位（其實這邊不一定要存進 df，只是方便檢查）
    df = add_lex_feats_to_df(df, word2logodds, text_col=TEXT_COL)

    # 載入模型
    tokenizer, model, device = load_lexicon_bert(model_dir)

    # 預測
    probs = predict_proba_food_for_texts(
        df[TEXT_COL].tolist(),
        tokenizer=tokenizer,
        model=model,
        word2logodds=word2logodds,
        device=device,
    )

    # 假設 label = 1 是食物評論
    df["proba_notfood"] = probs[:, 0]
    df["proba_food"] = probs[:, 1]

    # 根據 threshold 產生預測標籤（1=食物, 0=非食物）
    df["pred_food"] = (df["proba_food"] >= threshold).astype(int)

    # 存完整結果（含機率與 pred_food 標籤）
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"[saved] 帶預測機率與 pred_food 的結果已存到：{output_csv}")

    # 如果有指定 filtered_output_csv，就多存一份「只保留食物評論」的檔案
    df_food = None
    if filtered_output_csv is not None:
        df_food = df[df["pred_food"] == 1].copy()
        drop_cols = ["proba_notfood", "proba_food", "pred_food", "lex_feats"]
        df_food = df_food.drop(columns=drop_cols)
        df_food.to_csv(filtered_output_csv, index=False, encoding="utf-8-sig")
        print(f"[saved] 只保留預測為食物評論的結果已存到：{filtered_output_csv}")

    return df, df_food

