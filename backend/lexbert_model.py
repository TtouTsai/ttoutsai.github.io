# lexbert_model.py
import torch
import torch.nn as nn
from transformers import BertPreTrainedModel, BertModel


class LexiconEnhancedBertForSequenceClassification(BertPreTrainedModel):
    def __init__(self, config, lex_feat_dim=5):
        """
        lex_feat_dim：lexicon feature 維度（預設 5）
        """
        super().__init__(config)
        self.num_labels = config.num_labels
        self.bert = BertModel(config)

        # --- Multi-layer lexicon projection ---
        self.lex_proj = nn.Sequential(
            nn.Linear(lex_feat_dim, config.hidden_size // 2),
            nn.LayerNorm(config.hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(config.hidden_size // 2, config.hidden_size),
            nn.LayerNorm(config.hidden_size),
            nn.Tanh(),
        )

        # --- Attention mechanism for fusion ---
        self.attention = nn.MultiheadAttention(
            embed_dim=config.hidden_size,
            num_heads=8,
            dropout=0.1,
            batch_first=True,   # (batch, seq_len, hidden)
        )

        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier = nn.Linear(config.hidden_size, config.num_labels)

        self.post_init()

    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        token_type_ids=None,
        lex_feats=None,
        labels=None,
        **kwargs,
    ):
        # 先走原本 BERT
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )

        # sequence_output: (batch, seq_len, hidden)
        sequence_output = outputs.last_hidden_state
        # CLS 向量 (batch, hidden)
        cls_emb = sequence_output[:, 0, :]

        # ===== Lexicon Feature 融合 =====
        if lex_feats is not None:
            # lex_feats: (batch, lex_feat_dim)
            lex_emb = self.lex_proj(lex_feats)       # (batch, hidden)
            lex_emb = lex_emb.unsqueeze(1)           # (batch, 1, hidden)

            # attention_mask: 1=有效, 0=padding
            if attention_mask is not None:
                key_padding_mask = (attention_mask == 0)  # True → 忽略
            else:
                key_padding_mask = None

            fused, _ = self.attention(
                lex_emb,          # query:  (batch, 1, hidden)
                sequence_output,  # key:    (batch, seq_len, hidden)
                sequence_output,  # value:  (batch, seq_len, hidden)
                key_padding_mask=key_padding_mask,
            )  # fused: (batch, 1, hidden)

            # 殘差：用 lexicon 導出的 summary 校正 CLS
            cls_emb = cls_emb + fused.squeeze(1)     # (batch, hidden)

        cls_emb = self.dropout(cls_emb)
        logits = self.classifier(cls_emb)

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(
                logits.view(-1, self.num_labels),
                labels.view(-1),
            )

        return {"loss": loss, "logits": logits}
