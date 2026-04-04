from __future__ import annotations

from src.utils.mapper import RegulatoryMapper


class ConflictResolver:
    """Evaluates regulatory paradoxes within an audit sequence based on conflicts_with mapping."""

    def __init__(self, mapper: RegulatoryMapper):
        self.mapper = mapper

    def resolve(self, audit_trail: list) -> list:
        passed_controls: set = set()
        failed_controls: set = set()

        for item in audit_trail:
            control = item.get("regulatory_control", "")
            score = str(item.get("score", "")).upper()

            if "PASS" in score:
                passed_controls.add(control)
            elif "FAIL" in score:
                failed_controls.add(control)
            else:
                try:
                    num_score = float(score.split()[0])
                    if num_score >= 0.8:
                        passed_controls.add(control)
                    else:
                        failed_controls.add(control)
                except ValueError:
                    pass

        conflicts = []

        for _metric, data in self.mapper.mapping.items():
            control = data.get("control")
            conflicts_with = data.get("conflicts_with")

            if conflicts_with and control in passed_controls and conflicts_with in failed_controls:
                conflict_key = tuple(sorted([control, conflicts_with]))

                if not any(c.get("_key") == conflict_key for c in conflicts):
                    conflicts.append(
                        {
                            "_key": conflict_key,
                            "passed_control": control,
                            "failed_control": conflicts_with,
                            "reason": (
                                f"System strictly satisfied {control} but critically breached {conflicts_with}. "
                                "This signals a structural Regulatory Paradox "
                                "(e.g. over-explanation defeating privacy routines)."
                            ),
                        }
                    )

        return conflicts
