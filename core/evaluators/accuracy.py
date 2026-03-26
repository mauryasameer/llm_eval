import re
import json
import os

class FinancialNormalizer:
    """Normalizes financial string expressions into standard Python floats for reliable equivalence testing."""
    
    @staticmethod
    def normalize_amount(text: str):
        original_text = text
        text = text.lower().strip()
        # Remove currency symbols completely for pure numerical value
        text = re.sub(r'[$£€]', '', text).strip()
        
        multiplier = 1.0
        
        # Check scale words or letters
        if 'trillion' in text or text.endswith('t'):
            multiplier = 1e12
        elif 'billion' in text or text.endswith('b'):
            multiplier = 1e9
        elif 'million' in text or text.endswith('m'):
            multiplier = 1e6
        elif 'thousand' in text or text.endswith('k'):
            multiplier = 1e3
            
        # Strip out the scale text from the raw number
        text = re.sub(r'(trillion|billion|million|thousand|[tbmk])', '', text).strip()
        text = text.replace(" ", "")
        
        # Handle EU vs US numeric formats
        if ',' in text and '.' in text:
            if text.rfind(',') > text.rfind('.'):
                # EU format: 1.000.000,50
                text = text.replace('.', '').replace(',', '.')
            else:
                # US format: 1,000,000.50
                text = text.replace(',', '')
        elif ',' in text:
            # E.g. "1,000" (US thousand) vs "10,50" (EU decimal)
            if text.count(',') > 1 or (len(text) - text.rfind(',') == 4):
                text = text.replace(',', '')
            else:
                text = text.replace(',', '.')
                
        try:
            return float(text) * multiplier
        except ValueError:
            return original_text

def extract_entities(text: str) -> set:
    """Extract tickers, amounts, and dates from text and normalize them."""
    # Tickers
    tickers_raw = set(re.findall(r'\$?[A-Z]{2,5}\b', text))
    # Normalize $AAPL to AAPL for equivalent matching
    tickers = {t.replace('$', '') for t in tickers_raw}
    
    # Amounts
    amounts_raw = set(re.findall(r'[$£€]?\s*\d+(?:[.,]\d+)*(?:\s*(?:[kKmMbBtT]|thousand|million|billion|trillion))?\b', text, re.IGNORECASE))
    
    amounts = set()
    for a in amounts_raw:
        # Pass each matched numerical string token through the normalizer to return floats
        norm = FinancialNormalizer.normalize_amount(a)
        amounts.add(norm)
            
    # Dates
    dates_raw = set(re.findall(r'\b(?:Q[1-4]\s+\d{4}|\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{4}-\d{2}-\d{2})\b', text))
    dates = {d for d in dates_raw}
    
    return tickers.union(amounts).union(dates)

def evaluate_financial_f1(gold_standard: str, prediction: str, output_path: str = "accuracy_score.json") -> dict:
    gold_entities = extract_entities(gold_standard)
    pred_entities = extract_entities(prediction)
    
    # Base text words (excluding entities for simple word overlap)
    gold_words = set(re.findall(r'\b\w+\b', gold_standard.lower()))
    pred_words = set(re.findall(r'\b\w+\b', prediction.lower()))
    
    # Calculate weighted matches
    # Entities have 5x weight, normal words have 1x weight
    ENTITY_WEIGHT = 5
    WORD_WEIGHT = 1
    
    # Intersections
    matched_entities = gold_entities.intersection(pred_entities)
    matched_words = gold_words.intersection(pred_words)
    
    # Calculate scores
    true_positives = (len(matched_entities) * ENTITY_WEIGHT) + (len(matched_words) * WORD_WEIGHT)
    
    # False positives: in prediction but not in gold
    fp_entities = pred_entities - gold_entities
    fp_words = pred_words - gold_words
    false_positives = (len(fp_entities) * ENTITY_WEIGHT) + (len(fp_words) * WORD_WEIGHT)
    
    # False negatives: in gold but not in prediction
    fn_entities = gold_entities - pred_entities
    fn_words = gold_words - pred_words
    false_negatives = (len(fn_entities) * ENTITY_WEIGHT) + (len(fn_words) * WORD_WEIGHT)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    result = {
        "metric": "financial_f1",
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "details": {
            # Convert internal structures to strings to ensure JSON serialization compatibility
            "gold_entities": [str(e) for e in gold_entities],
            "pred_entities": [str(e) for e in pred_entities],
            "matched_entities": [str(e) for e in matched_entities]
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=4)
        
    return result

if __name__ == "__main__":
    # Diagnostic test for Normalizer Class logic
    print("Testing FinancialNormalizer...")
    tests = ["10 billion", "$10.5B", "1.000.000,00", "1,000,000.00", "500k", "1.5 million"]
    for t in tests:
        print(f" '{t}' -> {FinancialNormalizer.normalize_amount(t)}")
        
    # Evaluate new F1 extraction
    gold = "Apple ($AAPL) earned $10 Billion in Q3 2024."
    pred = "Apple (AAPL) made $10,000,000,000 in Q3 2024."
    print("\nEvaluating Financial-F1 end-to-end test case ($10 Billion vs $10,000,000,000)...")
    print(json.dumps(evaluate_financial_f1(gold, pred), indent=2))
