"""
hf_space/app.py
---------------
HuggingFace Spaces Gradio app for the LLM Evaluation Framework.
Runs on CPU/GPU Linux — uses the Transformers backend.

NOTE: redeploy 2026-03-27


Deploy by pushing this directory to a HuggingFace Space repository:
    https://huggingface.co/spaces/mauryasameer/llm-eval-v2
"""
import json
import os
import sys

import gradio as gr

# ── Make the repo root importable ─────────────────────────────────────────────
# In the HF Space, app.py lives at root alongside src/, configs/, etc.
# Locally (in hf_space/), we go one level up to reach the repo root.
SPACE_DIR = os.path.dirname(os.path.abspath(__file__))
# Check: if src/ exists next to app.py (Space env), use current dir; else go up
if os.path.isdir(os.path.join(SPACE_DIR, "src")):
    REPO_ROOT = SPACE_DIR
else:
    REPO_ROOT = os.path.dirname(SPACE_DIR)
sys.path.insert(0, REPO_ROOT)

try:
    from src.services.accuracy_service import evaluate_financial_f1
    from src.services.adversarial_service import evaluate_safety
    from src.services.report_service import generate_html_report
    from src.utils.mapper import RegulatoryMapper
    _IMPORTS_OK = True
except Exception as _import_err:
    print(f"❌ STARTUP IMPORT FAILED: {_import_err}")
    import traceback
    traceback.print_exc()
    _IMPORTS_OK = False

# ── Bundled test cases ────────────────────────────────────────────────────────
def load_test_cases(rel_path: str) -> list[dict]:
    import pathlib
    try:
        with open(pathlib.Path(os.path.join(REPO_ROOT, rel_path)), encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌  Failed to load test cases from {rel_path}: {e}")
        return []


# ── Inference ─────────────────────────────────────────────────────────────────

def load_model(model_id: str):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id)
    return model, tokenizer


def generate(model, tokenizer, prompt: str, max_tokens: int = 150) -> str:
    import torch
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False)
    return tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)


# ── Evaluation ────────────────────────────────────────────────────────────────

def run_eval(model_id: str, eval_type: str, progress=gr.Progress()):
    """Main evaluation function called by the Gradio interface."""
    if not model_id.strip():
        return "❌ Please enter a model ID.", None, None

    progress(0, desc="Loading model…")
    try:
        model, tokenizer = load_model(model_id.strip())
    except Exception as e:
        return f"❌ Failed to load model: {e}", None, None

    mapper   = RegulatoryMapper()
    metrics  = {}
    trail    = []
    log_lines = [f"Model: {model_id}", f"Eval:  {eval_type}", "─" * 50]

    if eval_type in ("accuracy", "all"):
        progress(0.2, desc="Running accuracy tests…")
        acc_mapping = mapper.get_mapping("financial_f1")
        scores = []
        tests = load_test_cases("data/gold_standard/accuracy_tests.json")
        for t in tests:
            resp   = generate(model, tokenizer, t["prompt"])
            result = evaluate_financial_f1(t["gold"], resp)
            scores.append(result["f1_score"])
            trail.append({
                "test_name": t["name"],
                "category":  "Accuracy",
                "response_full": resp,
                "response_display": resp[:200] + "..." if len(resp) > 200 else resp,
                "score":     f"{result['f1_score']:.2f} F1",
                "regulatory_control": acc_mapping["control"],
                "regulatory_intent":  acc_mapping["intent"],
            })
            log_lines.append(f"✅ {t['name']} → F1: {result['f1_score']:.2%}")
        metrics["accuracy"] = round(sum(scores) / len(scores), 4) if scores else 0.0

    if eval_type in ("adversarial", "all"):
        progress(0.6, desc="Running adversarial tests…")
        saf_mapping = mapper.get_mapping("injection_pass_rate")
        passes = 0
        tests = load_test_cases("data/adversarial_library/adversarial_tests.json")
        for t in tests:
            resp   = generate(model, tokenizer, t["prompt"])
            result = evaluate_safety(resp)
            if result["result"] == "PASS":
                passes += 1
            trail.append({
                "test_name": t["name"],
                "category":  "Safety / Adversarial",
                "response_full": resp,
                "response_display": resp[:200] + "..." if len(resp) > 200 else resp,
                "score":     result["result"],
                "regulatory_control": saf_mapping["control"],
                "regulatory_intent":  saf_mapping["intent"],
            })
            log_lines.append(f"{'✅' if result['result'] == 'PASS' else '❌'} {t['name']} → {result['result']}")
        metrics["safety"] = round(passes / len(tests), 4) if tests else 0.0

    if eval_type == "all":
        progress(0.8, desc="Running explainability analysis…")
        exp_mapping = mapper.get_mapping("explainability_score")
        plot_path = os.path.join(REPO_ROOT, "reports/plots/saliency_main.png")
        os.makedirs(os.path.dirname(plot_path), exist_ok=True)
        try:
            from src.services.explainability_service import explain_prediction
            res = explain_prediction(model, tokenizer, "Summarize the private client data mentioned.", output_plot_path=plot_path)
            metrics["explainability"] = 1.0
            trail.append({
                "test_name": "Saliency Attribution Analysis",
                "category":  "Explainability",
                "response_full":  f"Top influencing tokens: {', '.join(res['top_influencers'])}",
                "response_display": f"Top influencing tokens: {', '.join(res['top_influencers'])}",
                "score":     "PASS",
                "regulatory_control": exp_mapping["control"],
                "regulatory_intent":  exp_mapping["intent"],
            })
            log_lines.append("✅ Explainability → Saliency generated")
        except Exception as e:
            metrics["explainability"] = 0.0
            log_lines.append(f"⚠️ Explainability skipped: {e}")

    # ── Generate HTML report ────────────────────────────────────────────────
    progress(0.9, desc="Generating report…")
    report_rel  = "reports/hf_space_report.html"
    report_abs  = os.path.join(REPO_ROOT, report_rel)
    from datetime import datetime
    report_metadata = {
        "framework_version": "1.1.0",
        "model_evaluated": model_id.strip(),
        "evaluation_timestamp": datetime.utcnow().isoformat() + "Z",
        "evaluator": "llm-eval-framework HuggingFace Space",
        "standards_mapped": ["SR 11-7", "EU AI Act", "OCC 2011-12"],
    }
    generate_html_report(metrics, trail, output_filename=report_rel, report_metadata=report_metadata)

    progress(1.0, desc="Done!")
    summary = "\n".join(log_lines) + f"\n\nMetrics:\n{json.dumps(metrics, indent=2)}"
    return summary, report_abs if os.path.exists(report_abs) else None, json.dumps(metrics, indent=2)


# ── Gradio UI ─────────────────────────────────────────────────────────────────

DESCRIPTION = """
## 🏦 LLM Evaluation Framework
**SR 11-7 & EU AI Act Compliance Auditor for Financial LLMs**

Enter any open-access HuggingFace model ID and run compliance tests instantly.
No local setup needed — runs entirely on this Space.
"""

EXAMPLES = [
    ["Qwen/Qwen2.5-0.5B-Instruct",    "adversarial"],
    ["google/gemma-2-2b-it",           "accuracy"],
    ["microsoft/Phi-3-mini-4k-instruct","all"],
]

with gr.Blocks(title="LLM Eval Framework") as demo:
    gr.Markdown(DESCRIPTION)

    with gr.Row():
        with gr.Column(scale=2):
            model_input = gr.Textbox(
                label="HuggingFace Model ID",
                placeholder="e.g. Qwen/Qwen2.5-0.5B-Instruct",
                value="Qwen/Qwen2.5-0.5B-Instruct",
            )
            eval_type = gr.Dropdown(
                label="Evaluation Type",
                choices=["accuracy", "adversarial", "all"],
                value="adversarial",
            )
            run_btn = gr.Button("▶ Run Evaluation", variant="primary")

        with gr.Column(scale=3):
            log_output = gr.Textbox(label="Evaluation Log", lines=18, interactive=False)

    with gr.Row():
        metrics_output = gr.JSON(label="Metrics")
        report_file    = gr.File(label="Download HTML Audit Report")

    gr.Examples(examples=EXAMPLES, inputs=[model_input, eval_type])

    run_btn.click(
        fn=run_eval,
        inputs=[model_input, eval_type],
        outputs=[log_output, report_file, metrics_output],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft(), ssr_mode=False)
