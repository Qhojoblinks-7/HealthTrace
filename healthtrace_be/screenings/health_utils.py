def calculate_bmi(weight_kg, height_cm):
    """
    Compute BMI from weight (kg) and height (cm).
    Returns float rounded to 1 decimal place.
    """
    try:
        weight = float(weight_kg)
        height = float(height_cm)
        if weight <= 0 or height <= 0:
            return None
        height_m = height / 100
        bmi = weight / (height_m * height_m)
        return round(bmi, 1)
    except (ValueError, TypeError):
        return None


def get_bmi_category(bmi):
    """
    Categorize BMI per WHO standards:
    - Underweight: < 18.5
    - Normal: 18.5 - 24.9
    - Overweight: 25 - 29.9
    - Obese: >= 30
    """
    if bmi is None:
        return None
    if bmi < 18.5:
        return 'Underweight'
    if bmi < 25:
        return 'Normal'
    if bmi < 30:
        return 'Overweight'
    return 'Obese'


def get_blood_pressure_status(systolic, diastolic):
    """
    Categorize blood pressure per AHA guidelines:
    - Normal: Systolic < 120 AND Diastolic < 80
    - Elevated: Systolic 120-129 AND Diastolic < 80
    - Stage 1: Systolic 130-139 OR Diastolic 80-89
    - Stage 2: Systolic >= 140 OR Diastolic >= 90
    - Crisis: Systolic > 180 OR Diastolic > 120
    """
    try:
        sys_val = float(systolic)
        dia_val = float(diastolic)
    except (ValueError, TypeError):
        return None

    if sys_val > 180 or dia_val > 120:
        return 'Crisis'
    if sys_val >= 140 or dia_val >= 90:
        return 'Stage 2'
    if sys_val >= 130 or dia_val >= 80:
        return 'Stage 1'
    if sys_val >= 120 and dia_val < 80:
        return 'Elevated'
    return 'Normal'


def get_glucose_status(glucose):
    """
    Categorize blood glucose per ADA standards:
    - Normal: < 140 mg/dL
    - Prediabetes: 140 - 199 mg/dL
    - Diabetes: >= 200 mg/dL
    """
    try:
        g_val = float(glucose)
    except (ValueError, TypeError):
        return None

    if g_val >= 200:
        return 'Diabetes'
    if g_val >= 140:
        return 'Prediabetes'
    return 'Normal'


def evaluate_clinical_urgency(data):
    """
    Evaluate submitted dynamic key-value data against AHA/ADA emergency guidelines:
    - Systolic BP >= 180 mmHg or Diastolic BP >= 120 mmHg (Hypertensive Crisis)
    - Glucose >= 250 mg/dL or <= 70 mg/dL (Severe Hyper/Hypoglycemia)

    Returns True if any emergency threshold is met.
    """
    try:
        # Systolic Blood Pressure
        sys_val = data.get('systolic') or data.get('systolic_bp') or data.get('bp_sys')
        if sys_val is not None and float(sys_val) >= 180:
            return True

        # Diastolic Blood Pressure
        dia_val = data.get('diastolic') or data.get('diastolic_bp') or data.get('bp_dia')
        if dia_val is not None and float(dia_val) >= 120:
            return True

        # Glucose / Blood Sugar
        glucose_val = data.get('glucose') or data.get('glucose_level') or data.get('blood_sugar')
        if glucose_val is not None:
            g_num = float(glucose_val)
            if g_num >= 250 or g_num <= 70:
                return True

    except (ValueError, TypeError):
        pass

    return False
