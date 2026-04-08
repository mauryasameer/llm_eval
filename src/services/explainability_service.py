"""
explainability_service.py
-------------------------
Hardware-native saliency explainer for LLM token attribution.

Instead of slow SHAP perturbation, this module directly intercepts the
self-attention weights from the final transformer layer to compute a
per-token Saliency Score in a single forward pass.

Backends supported:
    - MLX (Apple Silicon / Metal GPU) — primary fast path
    - PyTorch / Transformers (CUDA / CPU) — cross-platform fallback
"""
from __future__ import annotations

import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.providers.mlx_provider import MLXSaliencyProvider
from src.providers.torch_provider import TorchSaliencyProvider

_mlx_provider = MLXSaliencyProvider()
_torch_provider = TorchSaliencyProvider()


def explain_prediction(
    model,
    tokenizer,
    prompt: str,
    output_plot_path: str = "reports/plots/influencers.png",
    top_k: int = 5,
) -> dict:
    """
    Compute an attention-based saliency map and return the top-k influential tokens.

    The function intercepts self-attention weights from the model's final
    transformer layer, averages across all heads, and ranks input tokens
    by their influence on the last generated token.

    Args:
        model: A loaded MLX or HuggingFace compatible model object.
        tokenizer: The corresponding tokenizer with encode/decode support.
        prompt: The input string to analyse.
        output_plot_path: File path for the saved horizontal bar chart.
        top_k: Number of top influential tokens to return (default: 5).

    Returns:
        A dict with keys:
            - 'top_influencers': list of the top_k token strings
            - 'plot_path': absolute path to the saved chart image

    Raises:
        ValueError: If the model architecture is unsupported.
    """
    os.makedirs(os.path.dirname(output_plot_path), exist_ok=True)

    # ── 1. Tokenize ──────────────────────────────────────────────────────────
    tokens = (
        tokenizer.encode(prompt)
        if hasattr(tokenizer, "encode")
        else tokenizer(prompt)["input_ids"]
    )

    if hasattr(tokenizer, "convert_ids_to_tokens"):
        token_strings = tokenizer.convert_ids_to_tokens(tokens)
    elif hasattr(tokenizer, "decode"):
        token_strings = [tokenizer.decode([t]) for t in tokens]
    else:
        token_strings = [str(t) for t in tokens]

    # ── 2. Detect backend ────────────────────────────────────────────────────
    saliency_scores: np.ndarray | None = _mlx_provider.compute(model, tokens)
    if saliency_scores is None:
        saliency_scores = _torch_provider.compute(model, tokens)

    # ── 3. Rank tokens ───────────────────────────────────────────────────────
    saliency_map = sorted(zip(token_strings, saliency_scores, strict=False), key=lambda x: x[1], reverse=True)

    top_tokens = [t for t, _ in saliency_map[:top_k]]

    # ── 4. Plot ──────────────────────────────────────────────────────────────
    chart_tokens = [t for t, _ in saliency_map[:10]][::-1]
    chart_values = [float(v) for _, v in saliency_map[:10]][::-1]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(chart_tokens, chart_values, color="#6366F1")
    ax.set_title("Self-Attention Saliency Drivers", fontsize=14, fontweight="bold")
    ax.set_xlabel("Mean Attention Weight (Final Layer)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_plot_path, dpi=150)
    plt.close(fig)

    return {"top_influencers": top_tokens, "plot_path": output_plot_path}
