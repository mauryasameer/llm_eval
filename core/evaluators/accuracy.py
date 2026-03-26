import re
import json
import os

def extract_entities(text: str) -> set:
    """Extract tickers, amounts, and dates from text."""
    # Tickers: $AAPL, MSFT (simplistic for caps 2-5 letters)
    tickers = set(re.findall(r'\$?[A-Z]{2,5}\b', text))
    
    # Amounts: $10B, £500m, €1.2k, 10.5M
    amounts = set(re.findall(r'[$£€]?\d+(?:\.\d+)?[kKmMbB]\b', text))
    
    # Dates: Q3 2024, 10/25, YYYY-MM-DD
    dates = set(re.findall(r'\b(?:Q[1-4]\s+\d{4}|\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{4}-\d{2}-\d{2})\b', text))
    
    return tickers.union(amounts).union(dates)

def evaluate_financial_f1(gold_standard: str, prediction: str, output_path: str = "accuracy_score.json") -> dict:
    gold_entities = extract_entities(gold_standard)
    pred_entities = extract_entities(prediction)
    
    # Base text words (excluding entities for simple word overlap)
    gold_words = set(re.findall(r'\w+', gold_standard.lower()))
    pred_words = set(re.findall(r'\w+', prediction.lower()))
    
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
            "gold_entities": list(gold_entities),
            "pred_entities": list(pred_entities),
            "matched_entities": list(matched_entities)
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=4)
        
    return result

if __name__ == "__main__":
    # Test
    gold = "Apple ($AAPL) earned £10B in Q3 2024."
    pred = "Apple (AAPL) made $10B in Q3 2024."
    print("Evaluating Financial-F1 test case...")
    print(json.dumps(evaluate_financial_f1(gold, pred), indent=2))
