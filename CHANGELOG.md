# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-04

### Added
- Initial release of LLM Evaluation & Validation Framework for Financial Services
- `FinancialNormalizer` and `evaluate_financial_f1` for weighted entity-level F1 scoring
- `evaluate_safety` adversarial prompt injection evaluator
- Attention-based saliency explainability module (MLX + PyTorch backends)
- Jinja2 HTML report generator with audit trail
- `ConflictResolver` for detecting regulatory paradoxes (SR 11-7 vs EU AI Act vs GDPR)
- `RegulatoryMapper` for YAML-driven metric-to-control mapping
- Gradio web UI deployed to HuggingFace Spaces
- Google Colab demo notebook
- GitHub Actions CI (pytest) and HuggingFace Space deploy workflows

[0.1.0]: https://github.com/mauryasameer/llm_eval/releases/tag/v0.1.0
