# 🛡️ llm-eval-framework
### **LLM Evaluation & Validation Framework for Financial Services**
**An opinionated, local-first auditing suite for SR 11-7 and EU AI Act Compliance.**

---

## 📖 Overview
The **llm-eval-framework** is a developer-first tool designed to bridge the gap between "experimental AI" and "regulated production." Built specifically for the high-stakes environment of Financial Services, it transforms raw LLM outputs into **Model Risk Management (MRM)** artifacts.

This framework is **local-first**, optimized for **Apple Silicon (M2/M3)** via `mlx-lm`, ensuring that sensitive financial data never leaves your hardware during the validation process.

### **The Problem it Solves**
In banking, "it works" is not a valid test result. You must prove *why* it works, *how* it fails, and *where* it sits in the regulatory landscape (**SR 11-7**, **OCC 2011-12**, **EU AI Act**). This framework automates the generation of that proof.

---

## 🏗️ System Architecture
The framework follows a modular "Auditor-in-the-Loop" design:

1.  **Inference Wrapper:** Standardized local inference using `mlx-lm` (Metal-optimized).
2.  **The Registry:** A `YAML` source of truth mapping metrics to regulatory clauses.
3.  **Evaluator Modules:**
    * **Accuracy:** Financial-F1 (Entity extraction integrity for tickers/amounts).
    * **Adversarial:** 50+ Red-teaming templates (Jailbreaks/PII leaks).
    * **Explainability:** SHAP/LIME token-level attribution.
4.  **Reporting Engine:** Jinja2-based generator for "Committee-Ready" HTML/PDF reports.

---

## 📂 Project Structure
```text
llm-eval-framework/
├── configs/
│   ├── regulatory_mapping.yaml  # Bridges Metrics -> SR 11-7 / EU AI Act
│   └── system_prompts.yaml      # Hardened guardrails for local models
├── core/
│   ├── evaluators/
│   │   ├── accuracy.py          # Financial-F1 & Entity extraction logic
│   │   ├── adversarial.py       # Prompt injection & Red-Teaming suite
│   │   └── explainability.py    # SHAP/LIME wrappers for token importance
│   ├── models/
│   │   └── local_mlx.py         # M2-optimized inference wrapper
│   └── report_engine/
│       └── generator.py         # Data-to-HTML/PDF compiler
├── data/
│   ├── adversarial_library/     # 50+ JSON-based jailbreak templates
│   └── gold_standard/           # Reference datasets for finance
├── reports/
│   ├── plots/                   # Generated SHAP/LIME visualizations
│   └── validation_report.html   # Final Audit Artifact
├── main.py                      # CLI Entry Point
└── requirements.txt             # Local-first dependencies (MLX, DeepEval, etc.)

```

---

## 🚀 Getting Started (MacBook Air M2/M3)

### 1. Prerequisites

* **Python 3.10+**
* **Apple Silicon (M2/M3)**
* **Antigravity IDE**

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/mauryasameer/llm_eval.git
cd llm-eval-framework

# Setup Virtual Environment
python -m venv venv
source venv/bin/activate

# Install Core Dependencies
pip install mlx-lm deepeval shap jinja2 pandas matplotlib

```

### 3. Running a Validation Audit

```bash
# Run the full validation suite (Accuracy + Adversarial)
python main.py --eval all --model mlx-community/Llama-3.2-3B-Instruct-4bit

```

---

## 🛠️ The 5 Core Modules

### **1. Accuracy Evaluator (Financial-F1)**

Standard NLP metrics ignore "Precision Severity." This module extracts Tickers, ISINs, and Monetary values, penalizing a `$10B` vs `$10M` error significantly higher than a grammatical one.

### **2. Adversarial Tester (Red-Teaming)**

A library of 50+ adversarial templates including:

* **Fiduciary Bypass:** Attempts to force unauthorized investment advice.
* **Data Leak Persona:** Trick the model into revealing mock PII.
* **System Override:** Testing resistance to instructions like "Ignore all previous safety rules."

### **3. Explainability Auditor**

Generates **SHAP** plots showing which input tokens (e.g., "Interest Rate," "Default") most heavily influenced the model's decision. Required for **Interpretability** under SR 11-7 Section 3.3.

### **4. Regulatory Mapping**

A `YAML` bridge that tags every technical test with a legal requirement:

* `financial_f1` ➡️ **SR 11-7 Section 3.2**
* `injection_pass_rate` ➡️ **EU AI Act Article 15**

### **5. HTML Validation Report**

A professional, glass-morphic report featuring:

* **Executive Summary:** Pass/Fail badges.
* **Risk Heatmap:** Visualizing Accuracy vs. Safety.
* **Audit Trail:** A table linking model responses directly to regulatory controls.

---

## 🛡️ Compliance Standards

| Regulation | Module | Focus Area |
| --- | --- | --- |
| **SR 11-7** | Accuracy / Explainability | Model Soundness & Interpretability |
| **EU AI Act** | Adversarial / Security | Robustness & Cybersecurity |
| **OCC 2011-12** | Reporting | Audit Trail & Documentation |

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 📈 Social Support

If you're using this to harden your local LLMs, tag us on LinkedIn!
**#GenerativeAI #ModelRisk #SR117 #OpenSource #LocalLLM**
