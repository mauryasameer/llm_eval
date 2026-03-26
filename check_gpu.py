"""
check_gpu.py
------------
Utility script to verify that hardware acceleration is available and functioning.
Supports MLX (Apple Silicon) with a graceful fallback message for other platforms.
"""
import sys


def check_hardware_acceleration() -> bool:
    """
    Detect and test the available ML hardware acceleration backend.

    Returns:
        True if hardware acceleration is functional, False otherwise.
    """
    # --- Apple Silicon / MLX ---
    try:
        import mlx.core as mx
        device = mx.default_device()
        a = mx.array([1.0, 2.0, 3.0])
        b = mx.array([4.0, 5.0, 6.0])
        c = a + b
        mx.eval(c)  # Force materialization to confirm Metal dispatch
        print(f"[MLX] Active device  : {device}")
        print(f"[MLX] Test operation : {a.tolist()} + {b.tolist()} = {c.tolist()}")
        print("✅  MLX / Metal GPU acceleration is active and ready for inference.")
        return True
    except ImportError:
        pass
    except Exception as exc:
        print(f"❌  MLX detected but encountered an error: {exc}", file=sys.stderr)
        return False

    # --- CUDA / PyTorch fallback ---
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"[PyTorch] CUDA device : {device_name}")
            print("✅  CUDA GPU acceleration is active and ready for inference.")
            return True
        else:
            print("[PyTorch] CUDA not available — running on CPU.")
            print("⚠️  No GPU acceleration detected. Inference will be slower.")
            return False
    except ImportError:
        pass

    print("⚠️  No supported ML acceleration backend found (MLX or PyTorch). CPU only.")
    return False


if __name__ == "__main__":
    print("=" * 56)
    print("  LLM Eval Framework — Hardware Acceleration Check")
    print("=" * 56)
    success = check_hardware_acceleration()
    sys.exit(0 if success else 1)
