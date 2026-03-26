import os
import numpy as np
import matplotlib.pyplot as plt
import shap

def explain_prediction(model, tokenizer, prompt: str, target_output: str, output_plot_path: str = "reports/plots/influencers.png"):
    """
    Run SHAP to explain which tokens in the `prompt` most influenced the `target_output`.
    """
    # Ensure plot directory exists
    os.makedirs(os.path.dirname(output_plot_path), exist_ok=True)
    
    def f(texts):
        """
        SHAP evaluation function.
        Takes a list of perturbed prompts and returns an array of scores.
        """
        import mlx.core as mx
        scores = []
        for text in texts:
            # Simple mock score to ensure it runs if model is a mock
            if hasattr(model, 'mock'):
                scores.append([np.random.random() * 0.1])
                continue
                
            try:
                prompt_tokens = mx.array(tokenizer.encode(text))
                target_tokens = mx.array(tokenizer.encode(target_output))
                
                logits = model(prompt_tokens[None])
                # Get prediction probabilities for the next token
                next_token_logits = logits[0, -1, :]
                probs = mx.softmax(next_token_logits)
                
                # Fetch probability of the first token of our target string
                first_target_token = target_tokens[0].item()
                prob = probs[first_target_token].item()
                scores.append([prob])
            except Exception as e:
                scores.append([0.0])
                
        return np.array(scores)

    # We use a custom string masker as a fallback if the tokenizer isn't fully supported by shap
    # In production, shap.maskers.Text(tokenizer) works best if huggingface tokenizers are used.
    try:
        masker = shap.maskers.Text(tokenizer)
    except Exception:
        # Fallback simplistic masker
        masker = shap.maskers.Text(r"\W")

    explainer = shap.Explainer(f, masker)
    
    # Run SHAP on the prompt
    shap_values = explainer([prompt])
    
    # Extract values: shape is usually (1, num_tokens, 1)
    values = shap_values.values[0]
    if len(values.shape) > 1:
        values = values[:, 0]
        
    data_tokens = shap_values.data[0]
    
    # Identify Top 5 Influencer Tokens based on absolute SHAP value magnitude
    top_indices = np.argsort(np.abs(values))[-5:][::-1]
    top_tokens = [data_tokens[i] for i in top_indices]
    
    print(f"Top 5 Influencer Tokens: {top_tokens}")
    
    # Create an explainability plot
    plt.figure(figsize=(10, 6))
    
    # Sorting for a clean bar chart showing up to 10 top influencers
    chart_indices = np.argsort(np.abs(values))[-min(10, len(values)):] 
    chart_tokens = [data_tokens[i] for i in chart_indices]
    chart_values = [values[i] for i in chart_indices]
    
    colors = ['green' if val > 0 else 'red' for val in chart_values]
    plt.barh(chart_tokens, chart_values, color=colors)
    plt.title(f'SHAP Influencer Tokens for Output: "{target_output[:20]}..."')
    plt.xlabel('SHAP Value (Impact on prediction likelihood)')
    plt.tight_layout()
    plt.savefig(output_plot_path)
    print(f"Plot saved to {output_plot_path}")
    
    return {
        "top_influencers": top_tokens,
        "plot_path": output_plot_path
    }

if __name__ == "__main__":
    # Mock class to simulate an MLX model and tokenizer for verification tests
    class MockTokenizer:
        def encode(self, text):
            return [1, 2, 3] # mock token IDs
        def __call__(self, text):
            # For SHAP compatibility it sometimes expects dictionary return
            return {"input_ids": [1,2,3], "offset_mapping": [(0,1), (1,2), (2,3)]}
        def decode(self, ids):
            return "mock"
            
    class MockModel:
        mock = True
        
    print("Testing Explainability Auditor (SHAP/LIME)...")
    explain_prediction(
        model=MockModel(),
        tokenizer=MockTokenizer(),
        prompt="Analyze the earnings report for Q3 EBITDA.",
        target_output="EBITDA jumped 15%.",
        output_plot_path="reports/plots/mock_influencers.png"
    )
