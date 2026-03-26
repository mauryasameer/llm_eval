"""
scripts/download_model.py
--------------------------
CLI tool to download a HuggingFace model and cache it locally for offline inference.

Automatically detects the correct backend:
  - Apple Silicon (macOS arm64) → downloads via mlx-lm (Metal-optimized)
  - Linux / Windows (CUDA / CPU) → downloads via HuggingFace Transformers

Usage:
    # Download the default recommended model
    python scripts/download_model.py

    # Download a specific model by HuggingFace ID
    python scripts/download_model.py --model mlx-community/Llama-3.2-3B-Instruct-4bit

    # List recommended models without downloading
    python scripts/download_model.py --list
"""
import argparse
import platform
import sys


# ── Recommended models per backend ───────────────────────────────────────────

RECOMMENDED_MODELS = {
    "mlx": [
        {
            "id": "mlx-community/Llama-3.2-3B-Instruct-4bit",
            "size": "~1.8 GB",
            "description": "Llama 3.2 3B (4-bit quantized) — best general-purpose choice",
        },
        {
            "id": "mlx-community/Qwen2.5-0.5B-Instruct-4bit",
            "size": "~0.4 GB",
            "description": "Qwen 2.5 0.5B (4-bit quantized) — ultra-lightweight, fast testing",
        },
        {
            "id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
            "size": "~4.1 GB",
            "description": "Mistral 7B (4-bit quantized) — best quality, needs 16GB+ RAM",
        },
    ],
    "transformers": [
        {
            "id": "meta-llama/Llama-3.2-1B-Instruct",
            "size": "~2.5 GB",
            "description": "Llama 3.2 1B — good CPU/CUDA baseline (gated, requires HF login)",
        },
        {
            "id": "Qwen/Qwen2.5-0.5B-Instruct",
            "size": "~1.0 GB",
            "description": "Qwen 2.5 0.5B — ultra-lightweight, open access",
        },
        {
            "id": "mistralai/Mistral-7B-Instruct-v0.3",
            "size": "~15 GB",
            "description": "Mistral 7B — best quality, needs 16GB+ VRAM / RAM",
        },
    ],
}


def detect_backend() -> str:
    """Return 'mlx' on Apple Silicon, 'transformers' otherwise."""
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        try:
            import mlx.core  # noqa: F401
            return "mlx"
        except ImportError:
            pass
    return "transformers"


def print_recommended(backend: str) -> None:
    models = RECOMMENDED_MODELS[backend]
    print(f"\n📦 Recommended models for your platform ({backend.upper()}):\n")
    for i, m in enumerate(models, 1):
        print(f"  {i}. {m['id']}")
        print(f"     Size: {m['size']}")
        print(f"     {m['description']}\n")
    print(f"Run:  python scripts/download_model.py --model <model_id>")


def download_mlx(model_id: str) -> None:
    try:
        from mlx_lm import load
    except ImportError:
        print("❌  mlx-lm not installed. Run: pip install mlx-lm", file=sys.stderr)
        sys.exit(1)

    print(f"⬇️   Downloading '{model_id}' via mlx-lm...")
    print("     (Model will be cached in ~/.cache/huggingface/)\n")
    model, tokenizer = load(model_id)
    print(f"\n✅  Model '{model_id}' is cached and ready for offline inference.")
    print("    Use it in your scripts with:")
    print(f"    from mlx_lm import load")
    print(f"    model, tokenizer = load('{model_id}')")


def download_transformers(model_id: str) -> None:
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        print("❌  transformers not installed. Run: pip install transformers", file=sys.stderr)
        sys.exit(1)

    print(f"⬇️   Downloading '{model_id}' via HuggingFace Transformers...")
    print("     (Model will be cached in ~/.cache/huggingface/)\n")
    AutoTokenizer.from_pretrained(model_id)
    AutoModelForCausalLM.from_pretrained(model_id)
    print(f"\n✅  Model '{model_id}' is cached and ready for offline inference.")
    print("    Use it in your scripts with:")
    print(f"    from transformers import AutoModelForCausalLM, AutoTokenizer")
    print(f"    tokenizer = AutoTokenizer.from_pretrained('{model_id}')")
    print(f"    model = AutoModelForCausalLM.from_pretrained('{model_id}')")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download a HuggingFace model for local inference.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="HuggingFace model ID to download (e.g. mlx-community/Llama-3.2-3B-Instruct-4bit)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List recommended models for your platform and exit",
    )
    parser.add_argument(
        "--backend",
        choices=["mlx", "transformers"],
        default=None,
        help="Force a specific download backend (default: auto-detect)",
    )

    args = parser.parse_args()
    backend = args.backend or detect_backend()

    print(f"🔍  Detected backend: {backend.upper()}")

    if args.list or args.model is None:
        print_recommended(backend)
        if args.model is None and not args.list:
            print("\nNo --model specified. Use --model <id> to download, or --list to see options.")
        sys.exit(0)

    if backend == "mlx":
        download_mlx(args.model)
    else:
        download_transformers(args.model)


if __name__ == "__main__":
    main()
