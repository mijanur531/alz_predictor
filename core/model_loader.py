import time

def predict_alzheimer(features: dict) -> dict:
    """
    Mock model inference for academic/portfolio purposes.
    Calculates Alzheimer's Risk class and probability score using clinical rules.
    """
    # Simulate slight processing delay for DL model feel
    time.sleep(1.2)
    
    # Feature extraction with defaults
    age = int(features.get('age', 65))
    gender = features.get('gender', 'Male')
    education_level = features.get('education_level', "Bachelor's")
    bmi = float(features.get('bmi', 24.0))
    smoking = bool(features.get('smoking', False))
    cognitive_score = float(features.get('cognitive_score', 27.0))  # Max MMSE is 30
    family_history = bool(features.get('family_history', False))
    physical_activity = float(features.get('physical_activity', 3.0))  # hours/week

    # Weighted scoring algorithm
    risk_score = 0.0
    
    # 1. Cognitive score (MMSE) - strongest predictor
    # Standard: MMSE 25-30 is Normal, 20-24 is Mild, 10-19 is Moderate, <10 is Severe
    if cognitive_score < 10:
        risk_score += 0.55
    elif cognitive_score < 20:
        risk_score += 0.35
    elif cognitive_score < 25:
        risk_score += 0.18
    
    # 2. Age - older age increases risk
    if age > 80:
        risk_score += 0.20
    elif age > 70:
        risk_score += 0.12
    elif age > 60:
        risk_score += 0.06

    # 3. Family history
    if family_history:
        risk_score += 0.15

    # 4. Lifestyle factors (smoking, high BMI, low physical activity)
    if smoking:
        risk_score += 0.05
    if bmi > 30.0:
        risk_score += 0.05
    if physical_activity < 2.0:
        risk_score += 0.05

    # Bound risk score between 0.02 and 0.98
    risk_score = max(0.02, min(0.98, risk_score))

    # Categorize class
    if risk_score >= 0.50:
        prediction_class = "Dementia"
        probability = risk_score
    elif risk_score >= 0.20:
        prediction_class = "MCI"  # Mild Cognitive Impairment
        probability = risk_score
    else:
        prediction_class = "Normal"
        probability = 1.0 - risk_score  # High probability of being healthy

    return {
        "class": prediction_class,
        "probability": round(probability, 3),
        "version": "v1.2.0-mock",
        "timestamp": time.time()
    }
