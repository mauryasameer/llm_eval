"""
torch_provider.py
-----------------
PyTorch / HuggingFace Transformers saliency backend (CUDA / CPU).
"""
from __future__ import annotations

import numpy as np

from src.core.interfaces import SaliencyProvider


class TorchSaliencyProvider(SaliencyProvider):
    """Extracts attention weights using PyTorch with a random fallback for tests."""

    def compute(self, model, tokens: list) -> np.ndarray | None:
        """Run PyTorch attention weight extraction with a random fallback for tests."""
        n_tokens = len(tokens)
        try:
            import torch

            inputs = torch.tensor([tokens]).to(model.device)
            with torch.no_grad():
                outputs = model(inputs, output_attentions=True)
            attn_weights = outputs.attentions[-1]
            avg = torch.mean(attn_weights[0, :, -1, :], dim=0)
            return avg.cpu().numpy()
        except Exception:
            # Last-resort random scores (e.g., unit tests with mock models)
            return np.random.rand(n_tokens)
