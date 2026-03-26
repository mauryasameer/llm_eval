import sys
import os

# Ensure mapper is accessible
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from core.utils.mapper import RegulatoryMapper

class ConflictResolver:
    """Evaluates regulatory paradoxes within an audit sequence based on conflicts_with mapping."""
    
    def __init__(self, mapper: RegulatoryMapper):
        self.mapper = mapper
        
    def resolve(self, audit_trail: list) -> list:
        passed_controls = set()
        failed_controls = set()
        
        # Determine PASS/FAIL states across the audit trail
        for item in audit_trail:
            control = item.get("regulatory_control", "")
            score = str(item.get("score", "")).upper()
            
            # Simple heuristic for extraction scores vs PASS/FAIL tags
            if "PASS" in score:
                passed_controls.add(control)
            elif "FAIL" in score:
                failed_controls.add(control)
            else:
                # If it's numerical (e.g. 0.85 F1), assign PASS if >= 0.8
                try:
                    num_score = float(score.split()[0])
                    if num_score >= 0.8:
                        passed_controls.add(control)
                    else:
                        failed_controls.add(control)
                except ValueError:
                    pass
                    
        conflicts = []
        
        # Evaluate overlapping constraints natively
        for metric, data in self.mapper.mapping.items():
            control = data.get("control")
            conflicts_with = data.get("conflicts_with")
            
            if conflicts_with and control in passed_controls and conflicts_with in failed_controls:
                # To prevent duplicates from bidirectional mappings, we order the tuple
                conflict_key = tuple(sorted([control, conflicts_with]))
                
                # Check if we already registered this paradox
                if not any(c.get("_key") == conflict_key for c in conflicts):
                    conflicts.append({
                        "_key": conflict_key,
                        "passed_control": control,
                        "failed_control": conflicts_with,
                        "reason": f"System strictly satisfied {control} but critically breached {conflicts_with}. This signals a structural Regulatory Paradox (e.g. over-explanation defeating privacy routines)."
                    })
                    
        return conflicts
