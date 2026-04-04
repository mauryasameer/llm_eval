from __future__ import annotations

import os

import yaml


class RegulatoryMapper:
    def __init__(self, config_path: str | None = None):
        if config_path is None:
            # Default to configs/regulatory_mapping.yaml relative to repo root
            config_path = os.path.join(os.path.dirname(__file__), "../../configs/regulatory_mapping.yaml")

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # Create a fast lookup dictionary
        self.mapping = {item["metric"]: item for item in self.config.get("mapping", [])}

    def get_mapping(self, metric: str) -> dict:
        """Fetch regulatory mapping strings for a specific metric."""
        return self.mapping.get(
            metric,
            {
                "metric": metric,
                "control": "Unknown",
                "intent": "No regulatory mapping found.",
            },
        )


if __name__ == "__main__":
    mapper = RegulatoryMapper()
    print("financial_f1:", mapper.get_mapping("financial_f1"))
    print("injection_pass_rate:", mapper.get_mapping("injection_pass_rate"))
