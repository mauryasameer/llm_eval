"""
scripts/download_model.py
--------------------------
CLI tool to download a HuggingFace model into the local `models/` directory
for offline inference. The `models/` folder is git-ignored so weights are
never pushed to the repository.

Automatically detects the correct backend:
  - Apple Silicon (macOS arm64) -> downloads via mlx-lm (Metal-optimized)
  - Linux / Windows (CUDA / CPU) -> downloads via HuggingFace Transformers

Usage:
    # See recommended models for your hardware
    python scripts/download_model.py --list

    # Download a model into models/<name>/ inside this repo (default)
    python scripts/download_model.py --model mlx-community/Llama-3.2-3B-Instruct-4bit

    # Use the global HuggingFace cache (~/.cache/huggingface/) instead
    python scripts/download_model.py --model mlx-community/Llama-3.2-3B-Instruct-4bit --global

    # Force a specific backend
    python scripts/download_model.py --model Qwen/Qwen2.5-0.5B-Instruct --backend transformers
"""
import argparse
import os
import platform
import sys

# ── Repo root (one level up from this script) ─────────────────────────────────
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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


def local_model_path(model_id: str) -> str:
    """Return the local path models/<sanitised_id>/ inside the repo."""
    safe_name = model_id.replace("/", "--")
    return os.path.join(_REPO_ROOT, "models", safe_name)


def print_recommended(backend: str) -> None:
    models = RECOMMENDED_MODELS[backend]
    print(f"\n📦 Recommended models for your platform ({backend.upper()}):\n")
    for i, m in enumerate(models, 1):
        print(f"  {i}. {m['id']}")
        print(f"     Size: {m['size']}")
        print(f"     {m['description']}\n")
    print("Run:  python scripts/download_model.py --model <model_id>")


def download_mlx(model_id: str, use_global_cache: bool = False) -> None:
    try:
        from mlx_lm import load
    except ImportError:
        print("❌  mlx-lm not installed. Run: pip install mlx-lm", file=sys.stderr)
        sys.exit(1)

    if use_global_cache:
        save_path = model_id
        print(f"⬇️   Downloading '{model_id}' via mlx-lm...")
        print("     Saving to: ~/.cache/huggingface/ (global cache)\n")
        load(save_path)
        print(f"\n✅  Done! Load with:")
        print(f"    from mlx_lm import load")
        print(f"    model, tokenizer = load('{model_id}')")
    else:
        save_path = local_model_path(model_id)
        os.makedirs(save_path, exist_ok=True)
        print(f"⬇️   Downloading '{model_id}' via mlx-lm...")
        print(f"     Saving to: models/{model_id.replace('/', '--')}/ (git-ignored)\n")
        load(model_id, model_path=save_path)
        print(f"\n✅  Done! Load with:")
        print(f"    from mlx_lm import load")
        print(f"    model, tokenizer = load('{save_path}')")


def download_transformers(model_id: str, use_global_cache: bool = False) -> None:
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        print("❌  transformers not installed. Run: pip install transformers", file=sys.stderr)
        sys.exit(1)

    if use_global_cache:
        cache_dir = None
        print(f"⬇️   Downloading '{model_id}' via HuggingFace Transformers...")
        print("     Saving to: ~/.cache/huggingface/ (global cache)\n")
    else:
        cache_dir = local_model_path(model_id)
        os.makedirs(cache_dir, exist_ok=True)
        print(f"⬇️   Downloading '{model_id}' via HuggingFace Transformers...")
        print(f"     Saving to: models/{model_id.replace('/', '--')}/ (git-ignored)\n")

    AutoTokenizer.from_pretrained(model_id, cache_dir=cache_dir)
    AutoModelForCausalLM.from_pretrained(model_id, cache_dir=cache_dir)

    load_path = cache_dir if cache_dir else model_id
    print(f"\n✅  Done! Load with:")
    print(f"    from transformers import AutoModelForCausalLM, AutoTokenizer")
    print(f"    tokenizer = AutoTokenizer.from_pretrained('{load_path}')")
    print(f"    model = AutoModelForCausalLM.from_pretrained('{load_path}')")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download a HuggingFace model into models/ (git-ignored) for offline use.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="HuggingFace model ID (e.g. mlx-community/Llama-3.2-3B-Instruct-4bit)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List recommended models for your platform and exit",
    )
    parser.add_argument(
        "--global", "-g",
        dest="use_global_cache",
        action="store_true",
        help="Save to ~/.cache/huggingface/ instead of the local models/ directory",
    )
    parser.add_argument(
        "--backend",
        choices=["mlx", "transformers"],
        default=None,
        help="Force a specific backend (default: auto-detect from hardware)",
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
        download_mlx(args.model, use_global_cache=args.use_global_cache)
    else:
        download_transformers(args.model, use_global_cache=args.use_global_cache)


if __name__ == "__main__":
    main()
