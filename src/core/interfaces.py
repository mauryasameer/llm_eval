"""
interfaces.py
-------------
Abstract base classes for all pluggable components in the evaluation framework.

New providers and services must implement the relevant interface defined here.
This keeps services testable (mock the interface) and prevents vendor lock-in.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class SaliencyProvider(ABC):
    """Interface for backend-specific attention saliency computation."""

    @abstractmethod
    def compute(self, model, tokens: list) -> np.ndarray | None:
        """
        Compute per-token saliency scores from model attention weights.

        Args:
            model: A loaded model object (MLX or HuggingFace compatible).
            tokens: List of token IDs for the input prompt.

        Returns:
            A 1-D numpy array of saliency scores (one per token),
            or None if this provider cannot handle the given model.
        """
        ...
