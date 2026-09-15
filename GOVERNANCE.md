# GOVERNANCE.md

## Intended Use

This framework supports a human compliance reviewer's judgment of an LLM's output quality
and safety — it does not autonomously approve, deploy, or act on a model based on its own
results. Every generated report (`reports/validation_report_*.html`) is decision support
for someone deciding whether a given model is fit for a financial-services use case, not an
automated go/no-go gate.

## Explainability Boundary

The Explainability module does not use SHAP or LIME, despite earlier documentation
suggesting otherwise — it computes a per-token saliency score by directly reading the final
transformer layer's self-attention weights (`src/providers/mlx_provider.py`,
`src/providers/torch_provider.py`), not by perturbation-based attribution. This describes
*which tokens the model attended to most* when producing its output — a statement about
the model's internal attention pattern, not a causal or business explanation of why the
model's conclusion is correct.

## Fairness

This framework evaluates the accuracy, safety, and explainability of LLM-generated text
against financial-domain test cases (entity extraction, adversarial prompts) — it does not
make or evaluate decisions about individuals, and the framework's own test data carries no
protected-attribute information. A disparate-impact fairness analysis does not apply to
this framework itself; if it's used to evaluate a model that will later be deployed in a
context that does make individual-level decisions, that downstream system needs its own
fairness analysis, which is outside this framework's scope.

## LLM Controls

Generation calls in `main.py::generate_response()` (both the MLX and torch/transformers
backends) do not set an explicit `temperature` or sampling parameter — they rely on the
underlying library's own default behavior. For a compliance-audit context where exact
reproducibility of a specific evaluation run matters, this is worth tightening in a future
pass; noted here rather than left unstated. The adversarial-testing module's prompts come
from a curated local test library (`data/adversarial_library/`), not live/untrusted
external input, so the prompt-injection surface for the framework's own operation is low —
the framework's actual purpose is testing how a model under evaluation responds to
adversarial prompts, which is a deliberate, controlled test, not an incidental exposure.

## Audit Trail

Every generated report already embeds a "Run Info"-style header (framework version, model
evaluated, evaluation timestamp) and a full audit-trail table listing every test case with
its result and mapped regulatory control (`src/services/report_service.py`,
`configs/regulatory_mapping.yaml`) — so a given report is traceable to what produced it.
The report also detects and surfaces "regulatory paradoxes" — cases where a run passes one
control but fails another the mapping marks as being in tension with it (e.g. maximizing
transparency directly undermining GDPR data-minimization) — via
`src/services/conflict_service.py`.

## Regulatory Framing

This is a financial-services LLM evaluation framework. `configs/regulatory_mapping.yaml`
names the applicable governance frameworks per metric: SR 11-7 (model risk management,
accuracy and explainability), the EU AI Act (technical robustness and transparency), and
GDPR (data minimization). `main.py`'s report metadata additionally references OCC 2011-12.
Naming these is not a compliance claim — it states which regulatory lens applies to each
metric this framework produces, so a reader knows the applicable frame.
