"""
main.py
-------
Main entry point for the LLM Evaluation Framework.

Orchestrates all evaluation modules (accuracy, adversarial, explainability)
against a local or HuggingFace model, then generates a full HTML audit report.

Usage:
    # Run all evaluations against a locally downloaded model
    python main.py --eval all --model models/mlx-community--Llama-3.2-3B-Instruct-4bit

    # Run only accuracy evaluation
    python main.py --eval accuracy --model models/mlx-community--Llama-3.2-3B-Instruct-4bit

    # Run adversarial tests only
    python main.py --eval adversarial --model mlx-community/Qwen2.5-0.5B-Instruct-4bit

    # Run all and save report to a custom path
    python main.py --eval all --model <path> --report reports/my_audit.html
"""
import argparse
import json
import os
import sys

# Ensure repo root is on path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.accuracy_service import evaluate_financial_f1
from src.services.adversarial_service import evaluate_safety
from src.services.report_service import generate_html_report
from src.utils.mapper import RegulatoryMapper

# ── Test Loading ──────────────────────────────────────────────────────────────

def load_test_cases(path: str) -> list[dict]:
    import pathlib
    try:
        with open(pathlib.Path(path), encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌  Failed to load test cases from {path}: {e}")
        sys.exit(1)

# ── Model loading ─────────────────────────────────────────────────────────────

def load_model(model_path: str):
    """Load model and tokenizer. Auto-detects MLX vs Transformers."""
    import platform
    is_apple_silicon = (platform.system() == "Darwin" and platform.machine() == "arm64")

    if is_apple_silicon:
        try:
            from mlx_lm import load
            print("  Backend : MLX (Apple Silicon)")
            model, tokenizer = load(model_path)
            return model, tokenizer, "mlx"
        except ImportError:
            pass

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        print(f"  Backend : Transformers ({'CUDA' if torch.cuda.is_available() else 'CPU'})")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path)
        return model, tokenizer, "transformers"
    except ImportError:
        print("❌  No ML backend found. Install mlx-lm (Mac) or transformers (other).")
        sys.exit(1)


def generate_response(model, tokenizer, prompt: str, backend: str, max_tokens: int = 200) -> str:
    """Run a single inference call and return the text response."""
    if backend == "mlx":
        from mlx_lm import generate
        return generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens, verbose=False)
    else:
        import torch
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=max_tokens)
        return tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)


# ── Evaluation modules ────────────────────────────────────────────────────────

def run_accuracy(model, tokenizer, backend: str, mapper: RegulatoryMapper, tests: list[dict]) -> tuple[dict, list]:
    print("\n🔬 [1/3] Running Accuracy Evaluation...")
    mapping = mapper.get_mapping("financial_f1")
    scores, trail = [], []

    for test in tests:
        print(f"   ▸ {test['name']}")
        response = generate_response(model, tokenizer, test["prompt"], backend)
        result = evaluate_financial_f1(test["gold"], response)
        scores.append(result["f1_score"])
        trail.append({
            "test_name": test["name"],
            "category": "Accuracy",
            "response_full": response,
            "response_display": response[:200] + "..." if len(response) > 200 else response,
            "score": f"{result['f1_score']:.2f} F1",
            "regulatory_control": mapping["control"],
            "regulatory_intent": mapping["intent"],
        })

    avg_f1 = sum(scores) / len(scores) if scores else 0.0
    print(f"   ✅ Average Financial F1: {avg_f1:.2%}")
    return {"accuracy": round(avg_f1, 4)}, trail



def run_adversarial(model, tokenizer, backend: str, mapper: RegulatoryMapper, tests: list[dict]) -> tuple[dict, list]:
    print("\n🛡️  [2/3] Running Adversarial Safety Evaluation...")
    saf_mapping = mapper.get_mapping("injection_pass_rate")
    pii_mapping = mapper.get_mapping("pii_masking_rate")
    passes, trail = 0, []

    for test in tests:
        print(f"   ▸ {test['name']}")
        response = generate_response(model, tokenizer, test["prompt"], backend)
        result = evaluate_safety(response)
        if result["result"] == "PASS":
            passes += 1
        # Use PII mapping for extraction-type prompts
        reg = pii_mapping if "PII" in test["name"] or "Extract" in test["name"] else saf_mapping
        trail.append({
            "test_name": test["name"],
            "category": "Safety / Adversarial",
            "response_full": response,
            "response_display": response[:200] + "..." if len(response) > 200 else response,
            "score": result["result"],
            "regulatory_control": reg["control"],
            "regulatory_intent": reg["intent"],
        })

    pass_rate = passes / len(tests)
    print(f"   ✅ Safety Pass Rate: {pass_rate:.2%} ({passes}/{len(tests)})")
    return {"safety": round(pass_rate, 4)}, trail



def run_explainability(model, tokenizer, backend: str, mapper: RegulatoryMapper) -> tuple[dict, list]:
    print("\n🔍 [3/3] Running Explainability / Saliency Analysis...")
    mapping = mapper.get_mapping("explainability_score")
    prompt = "Summarize the private client data mentioned in the system prompt."
    plot_path = "reports/plots/saliency_main.png"

    try:
        from src.services.explainability_service import explain_prediction
        result = explain_prediction(model, tokenizer, prompt, output_plot_path=plot_path)
        top = result["top_influencers"]
        print(f"   ✅ Top Saliency Tokens: {top}")
        score = 1.0
        trail_entry = {
            "test_name": "Saliency Attribution Analysis",
            "category": "Explainability",
            "response_full": f"Top influencing tokens: {', '.join(top)}",
            "response_display": f"Top influencing tokens: {', '.join(top)}",
            "score": "PASS",
            "regulatory_control": mapping["control"],
            "regulatory_intent": mapping["intent"],
        }
    except Exception as e:
        print(f"   ⚠️  Explainability skipped: {e}")
        score = 0.0
        trail_entry = {
            "test_name": "Saliency Attribution Analysis",
            "category": "Explainability",
            "response_full": f"Skipped: {str(e)}",
            "response_display": f"Skipped: {str(e)}",
            "score": "SKIP",
            "regulatory_control": mapping["control"],
            "regulatory_intent": mapping["intent"],
        }

    return {"explainability": score}, [trail_entry]


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="LLM Evaluation Framework — SR 11-7 & EU AI Act Compliance Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--model", "-m", required=True,
                        help="Path to local model dir or HuggingFace repo ID")
    parser.add_argument("--eval", "-e", default="all",
                        choices=["all", "accuracy", "adversarial", "explainability"],
                        help="Which evaluation module to run (default: all)")
    parser.add_argument("--report", "-r", default="reports/validation_report_latest.html",
                        help="Output path for the HTML audit report")
    parser.add_argument("--accuracy-tests",
                        default="data/gold_standard/accuracy_tests.json",
                        help="Path to accuracy test cases JSON")
    parser.add_argument("--adversarial-tests",
                        default="data/adversarial_library/adversarial_tests.json",
                        help="Path to adversarial test cases JSON")
    args = parser.parse_args()

    print("=" * 60)
    print("  LLM Evaluation Framework")
    print("  SR 11-7 & EU AI Act Compliance Auditor")
    print("=" * 60)
    print(f"\n  Model  : {args.model}")
    print(f"  Eval   : {args.eval}")
    print(f"  Report : {args.report}\n")

    print("📦 Loading model...")
    model, tokenizer, backend = load_model(args.model)

    mapper = RegulatoryMapper()
    all_metrics, all_trail = {}, []

    if args.eval in ("all", "accuracy"):
        acc_tests = load_test_cases(args.accuracy_tests)
        m, t = run_accuracy(model, tokenizer, backend, mapper, acc_tests)
        all_metrics.update(m)
        all_trail.extend(t)

    if args.eval in ("all", "adversarial"):
        adv_tests = load_test_cases(args.adversarial_tests)
        m, t = run_adversarial(model, tokenizer, backend, mapper, adv_tests)
        all_metrics.update(m)
        all_trail.extend(t)

    if args.eval in ("all", "explainability"):
        m, t = run_explainability(model, tokenizer, backend, mapper)
        all_metrics.update(m)
        all_trail.extend(t)

    print("\n📝 Generating Audit Report...")
    from datetime import datetime
    report_metadata = {
        "framework_version": "1.1.0",
        "model_evaluated": args.model,
        "evaluation_timestamp": datetime.utcnow().isoformat() + "Z",
        "evaluator": "llm-eval-framework Toolkit",
        "standards_mapped": ["SR 11-7", "EU AI Act", "OCC 2011-12"],
    }

    generate_html_report(all_metrics, all_trail, output_filename=args.report, report_metadata=report_metadata)

    # Write JSON Artifacts
    base_dir = os.path.dirname(args.report) or "."
    base_name = os.path.splitext(os.path.basename(args.report))[0]
    json_path = os.path.join(base_dir, f"{base_name}_trail.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_trail, f, indent=2)
    print(f"✅ Saved Raw JSON Audit Trail: {json_path}")

    print("\n" + "=" * 60)
    print("  Evaluation Complete!")
    print(f"  Metrics : {json.dumps(all_metrics, indent=2)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
