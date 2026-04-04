"""
mlx_provider.py
---------------
MLX (Apple Silicon / Metal GPU) saliency backend.
"""
from __future__ import annotations

import math

import numpy as np

from src.core.interfaces import SaliencyProvider


class MLXSaliencyProvider(SaliencyProvider):
    """Extracts attention weights using the MLX framework (Apple Silicon)."""

    def compute(self, model, tokens: list) -> np.ndarray | None:
        """Run MLX-native attention weight extraction. Returns None if MLX unavailable."""
        try:
            import mlx.core as mx
        except ImportError:
            return None

        if not (hasattr(model, "model") or hasattr(model, "layers")):
            return None

        m = model.model if hasattr(model, "model") else model
        x = mx.array([tokens])

        embed_fn = getattr(m, "embed_tokens", getattr(m, "tok_embeddings", None))
        if embed_fn is None:
            return None
        x = embed_fn(x)

        for layer in m.layers[:-1]:
            try:
                x = layer(x, mask=None, cache=None)
            except TypeError:
                x = layer(x)

        last_layer = m.layers[-1]

        norm_fn = getattr(last_layer, "input_layernorm", getattr(last_layer, "ln_1", None))
        norm_x = norm_fn(x) if norm_fn is not None else x

        attn = getattr(last_layer, "self_attn", getattr(last_layer, "attention", None))
        if attn is None:
            raise ValueError(
                "Cannot locate attention sub-module in final layer. "
                "Supported attribute names: 'self_attn', 'attention'."
            )

        B, L, D = norm_x.shape
        queries = attn.q_proj(norm_x)
        keys = attn.k_proj(norm_x)

        num_heads = getattr(attn, "num_heads", getattr(attn, "n_heads", 1))
        num_kv_heads = getattr(attn, "num_key_value_heads", getattr(attn, "n_kv_heads", num_heads))
        head_dim = D // num_heads

        queries = queries.reshape(B, L, num_heads, head_dim).transpose(0, 2, 1, 3)
        keys = keys.reshape(B, L, num_kv_heads, head_dim).transpose(0, 2, 1, 3)

        if num_kv_heads != num_heads:
            keys = mx.repeat(keys, num_heads // num_kv_heads, axis=1)

        scale = math.sqrt(head_dim)
        scores = (queries @ keys.transpose(0, 1, 3, 2)) / scale
        attention_weights = mx.softmax(scores, axis=-1)

        avg = mx.mean(attention_weights[0, :, -1, :], axis=0)
        return np.array(avg)
