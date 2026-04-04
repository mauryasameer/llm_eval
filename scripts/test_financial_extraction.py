import json
import os
import sys

from mlx_lm import generate, load

# Ensure core modules are accessible
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from core.evaluators.accuracy import evaluate_financial_f1
from core.utils.mapper import RegulatoryMapper


class LocalMLXModel:
    """Wrapper for a real MLX model using mlx-lm."""
    def __init__(self, model_path="mlx-community/Qwen2.5-0.5B-Instruct-4bit"):
        self.model_path = model_path
        print(f"Loading MLX model: '{self.model_path}'...")
        print("Note: If this is the first run, the model weights will be downloaded from HuggingFace.")
        self.model, self.tokenizer = load(self.model_path)
        print("Model loaded successfully!")

    def generate(self, prompt: str) -> str:
        """Generates a response using the loaded MLX model."""
        messages = [{"role": "user", "content": prompt}]

        # Format using the model's preferred chat template
        try:
            formatted_prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            formatted_prompt = f"User: {prompt}\nAssistant: "

        response = generate(self.model, self.tokenizer, prompt=formatted_prompt, max_tokens=100, verbose=False)
        return response.strip()


def main():
    # 1. Initialize the REAL MLX model (using a small, fast 4-bit model purely for testing)
    model = LocalMLXModel()

    # 2. Define the prompt and gold standard
    financial_statement = "In Q3 2024, Apple ($AAPL) reported total revenue of $10B."
    prompt = f"You are a strict financial analyst. Extract only the key financial entities (Tickers, Amounts, Dates) from the following text and return them in a short summary:\n\n{financial_statement}"
    gold_standard = "Apple ($AAPL) $10B Q3 2024"

    print("\nGenerating prediction from LocalMLXModel...")
    prediction = model.generate(prompt)
    print(f"Prediction: {prediction}\n")

    # 3. Evaluate using the Financial-F1 evaluator
    print("Running Financial-F1 Evaluation...")
    score_result = evaluate_financial_f1(
        gold_standard=gold_standard,
        prediction=prediction,
        output_path="accuracy_score.json" # temp local output
    )

    # 4. Attach Regulatory Mapping (SR 11-7 Section 3.2)
    mapper = RegulatoryMapper()
    mapping_info = mapper.get_mapping("financial_f1")

    # 5. Construct final artifact
    final_artifact = {
        "test_name": "Financial Entity Extraction Evaluation (Real MLX Model)",
        "model": model.model_path,
        "input_statement": financial_statement,
        "gold_standard": gold_standard,
        "prediction": prediction,
        "evaluation": score_result,
        "regulatory_compliance": mapping_info
    }

    # Save the composite artifact to the workspace
    artifact_path = os.path.join(os.path.dirname(__file__), '../validation_artifact.json')
    with open(artifact_path, 'w') as f:
        json.dump(final_artifact, f, indent=4)

    print(f"✅ Validation Artifact successfully saved to: {artifact_path}")
    print("\n--- Artifact Preview ---")
    print(json.dumps(final_artifact, indent=2))

if __name__ == "__main__":
    main()
