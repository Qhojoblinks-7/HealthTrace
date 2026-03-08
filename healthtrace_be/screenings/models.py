from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class Doctor(models.Model):
    """
    Doctor model for authentication and consultation tracking.
    Linked to Django's User model for authentication.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Doctor's contact number"
    )
    specialization = models.CharField(
        max_length=255,
        blank=True,
        help_text="Medical specialization (e.g., General Practitioner, Cardiologist)"
    )
    license_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Medical license number"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"


class Screening(models.Model):
    """
    Health screening model that stores patient health metrics
    and calculates BMI automatically.
    """
    
    # Gender choices
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    
    # ===============================
    # Personal & Demographic Data
    # ===============================
    full_name = models.CharField(
        max_length=255,
        help_text="Patient's full name for identification"
    )
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        help_text="Patient age in years"
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        help_text="Patient gender (Male/Female)"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Phone number for follow-up"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email address (optional)"
    )
    
    # ===============================
    # Physical Measurements
    # ===============================
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(10), MaxValueValidator(500)],
        help_text="Weight in kilograms"
    )
    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(50), MaxValueValidator(300)],
        help_text="Height in centimeters"
    )
    
    # ===============================
    # Vital Signs
    # ===============================
    systolic_bp = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(60), MaxValueValidator(250)],
        help_text="Systolic blood pressure (top number) in mmHg"
    )
    diastolic_bp = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(150)],
        help_text="Diastolic blood pressure (bottom number) in mmHg"
    )
    glucose_level = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(1000)],
        help_text="Blood glucose level in mg/dL"
    )
    heart_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(220)],
        help_text="Heart rate in BPM"
    )
    
    # ===============================
    # Qualitative Context
    # ===============================
    known_conditions = models.TextField(
        blank=True,
        null=True,
        help_text="Known conditions (e.g., Diabetes, Hypertension)"
    )
    current_medications = models.TextField(
        blank=True,
        null=True,
        help_text="Current medications the patient is taking"
    )
    
    # Additional notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes or observations"
    )
    
    # ===============================
    # Volunteer & Doctor Tracking
    # ===============================
    screened_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of the volunteer who performed the screening"
    )
    
    # Link to Doctor for consultation
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultations',
        help_text="Doctor who provided consultation"
    )
    doctor_advice = models.TextField(
        blank=True,
        null=True,
        help_text="Doctor's clinical impressions and recommended actions"
    )
    requires_specialist_followup = models.BooleanField(
        default=False,
        help_text="Whether the patient requires specialist follow-up"
    )
    consultation_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the doctor provided consultation"
    )
    
    # ===============================
    # Timestamps
    # ===============================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Screenings"
    
    def __str__(self):
        return f"{self.full_name} - {self.created_at.strftime('%Y-%m-%d')}"
    
    @property
    def bmi(self):
        """
        Calculate BMI (Body Mass Index).
        BMI = weight (kg) / height (m)^2
        """
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100  # Convert cm to m
            bmi_value = self.weight_kg / (height_m ** 2)
            return round(bmi_value, 2)
        return None
    
    @property
    def bmi_category(self):
        """
        Return BMI category based on WHO classification.
        """
        bmi_value = self.bmi
        if bmi_value is None:
            return "Unknown"
        elif bmi_value < 18.5:
            return "Underweight"
        elif bmi_value < 25:
            return "Normal weight"
        elif bmi_value < 30:
            return "Overweight"
        else:
            return "Obese"
    
    @property
    def blood_pressure_status(self):
        """
        Return blood pressure category based on American Heart Association guidelines.
        
        Category | Systolic (Top) | Diastolic (Bottom)
        ---------|----------------|-------------------
        Normal   | < 120          | < 80
        Elevated | 120-129        | < 80
        Stage 1  | 130-139        | OR 80-89
        Stage 2  | >= 140         | OR >= 90
        Crisis   | > 180          | OR > 120
        """
        systolic = self.systolic_bp
        diastolic = self.diastolic_bp
        
        if systolic is None or diastolic is None:
            return "Unknown"
        
        # Crisis takes priority
        if systolic > 180 or diastolic > 120:
            return "Hypertensive Crisis (Seek Immediate Care)"
        
        # Stage 2
        if systolic >= 140 or diastolic >= 90:
            return "High Blood Pressure Stage 2"
        
        # Stage 1
        if 130 <= systolic <= 139 or 80 <= diastolic <= 89:
            return "High Blood Pressure Stage 1"
        
        # Elevated
        if 120 <= systolic <= 129 and diastolic < 80:
            return "Elevated"
        
        # Normal
        if systolic < 120 and diastolic < 80:
            return "Normal"
        
        return "Unknown"
    
    @property
    def glucose_status(self):
        """
        Return blood glucose category based on American Diabetes Association guidelines.
        (Fasting glucose in mg/dL)
        
        Random Glucose Guide:
        Normal: < 140 mg/dL (< 7.8 mmol/L)
        Prediabetes: 140-199 mg/dL (7.8-11.0 mmol/L)
        Diabetes: >= 200 mg/dL (>= 11.1 mmol/L)
        """
        glucose = self.glucose_level
        
        if glucose is None:
            return "Unknown"
        
        if glucose < 140:
            return "Normal"
        elif glucose < 200:
            return "Prediabetes"
        else:
            return "Diabetes Indication"

    @property
    def is_critical(self):
        """
        Returns True if any vital sign is in crisis mode.
        Used to trigger red alerts in the frontend.
        """
        # Hypertensive Crisis
        if self.systolic_bp and (self.systolic_bp > 180 or self.diastolic_bp > 120):
            return True
        # Diabetic Crisis (Hyperglycemic crisis - typically >400 mg/dL)
        if self.glucose_level and self.glucose_level > 400:
            return True
        return False
    
    @property
    def has_consultation(self):
        """Returns True if a doctor has provided consultation."""
        return (self.doctor is not None and self.doctor_advice) or self.consultation_date is not None
