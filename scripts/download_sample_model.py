import sys
from mlx_lm import load

def download_sample_model(model_id="mlx-community/Llama-3.2-3B-Instruct-4bit"):
    print(f"Starting download and caching of '{model_id}' from HuggingFace...")
    print("This is a highly capable 3-Billion parameter model, optimized to run super fast on your Apple Silicon M2 Air!")
    print("Downloading weights... (This may take a few minutes depending on your internet speed)")
    
    # mlx_lm automatically fetches the model from HuggingFace and stores it in your local cache.
    model, tokenizer = load(model_id)
    
    print(f"\n✅ Success! The model {model_id} is now cached locally and ready for offline inference.")

if __name__ == "__main__":
    # You can change this to any supported mlx-community model ID.
    default_model = "mlx-community/Llama-3.2-3B-Instruct-4bit"
    download_sample_model(default_model)
