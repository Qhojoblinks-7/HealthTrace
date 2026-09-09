from django.db import models
from django.contrib.auth.models import User
import random
import string


class RoleConfig(models.Model):
    """
    Defines dynamic form inputs for a specific function.
    Schema example:
    [
        {"name": "systolic", "label": "Systolic BP", "type": "number", "required": True},
        {"name": "diastolic", "label": "Diastolic BP", "type": "number", "required": True}
    ]
    """
    role_name = models.CharField(max_length=100, unique=True, help_text="e.g., Vitals Intake, Optometry, General Consult")
    description = models.TextField(blank=True)
    schema = models.JSONField(default=list, help_text="List of field definitions for form rendering")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['role_name']

    def __str__(self):
        return self.role_name


class ScreeningStation(models.Model):
    """
    Dynamically configures physical tables for a health event.
    Admins can add, reorder, or remove stations per drive.
    """
    STATION_TYPE_CHOICES = [
        ('REGISTRATION', 'Table 1: Registration'),
        ('VITALS', 'Table 2: Vitals'),
        ('DOCTOR_TRIAGE', 'Table 3A: Doctor Triage'),
        ('LAB_GLUCOSE', 'Table 3B: Lab / Glucose'),
        ('DISCHARGE', 'Table 4: Admin Discharge'),
        ('GENERAL', 'General Checkout'),
    ]

    name = models.CharField(max_length=100, help_text="e.g., Table 1: Registration, Table 2: Blood Pressure")
    step_order = models.PositiveIntegerField(help_text="Order in the workflow (1, 2, 3...)")
    station_type = models.CharField(max_length=30, choices=STATION_TYPE_CHOICES, default='GENERAL', help_text="Functional type for routing logic")
    role_config = models.ForeignKey(RoleConfig, on_delete=models.PROTECT, help_text="Schema used at this station")
    is_final_discharge = models.BooleanField(default=False, help_text="Mark True if this is the Admin Discharge table")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['step_order']
        verbose_name = "Screening Station"
        verbose_name_plural = "Screening Stations"
        indexes = [
            models.Index(fields=['station_type', 'is_active']),
            models.Index(fields=['step_order']),
        ]

    def __str__(self):
        return f"Step {self.step_order}: {self.name}"

    def save(self, *args, **kwargs):
        from django.core.cache import cache
        cache.delete('registration_station')
        cache.delete('active_stations')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.cache import cache
        cache.delete('registration_station')
        cache.delete('active_stations')
        return super().delete(*args, **kwargs)


class PatientWorkflow(models.Model):
    """
    Represents a patient's overall state in the screening event.
    """
    token_id = models.CharField(max_length=20, unique=True, db_index=True, help_text="e.g., #A-104")
    patient_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True)

    # Dynamic Station Routing Pointer
    current_station = models.ForeignKey(
        ScreeningStation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='waiting_patients',
        help_text="The station where the patient is currently waiting or being served"
    )

    is_urgent = models.BooleanField(default=False, help_text="Flagged for emergency triage")
    is_completed = models.BooleanField(default=False, help_text="Marked True after final discharge")
    is_discharged = models.BooleanField(default=False, help_text="Locked after admin discharge; prevents post-exit edits")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_completed', 'is_discharged', '-created_at']),
            models.Index(fields=['current_station', 'is_completed']),
        ]

    def __str__(self):
        station_name = self.current_station.name if self.current_station else ("Completed" if self.is_completed else "Unassigned")
        return f"{self.token_id} - {self.patient_name} [{station_name}]"

    def save(self, *args, **kwargs):
        if not self.token_id:
            self.token_id = self.generate_token_id()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_token_id():
        for _ in range(5):
            prefix = random.choice(string.ascii_uppercase)
            number = random.randint(100, 999)
            token = f"#{prefix}-{number}"
            if not PatientWorkflow.objects.filter(token_id=token).exists():
                return token
        return f"#{random.choice(string.ascii_uppercase)}-{random.randint(100, 999)}"


class StationEntry(models.Model):
    """
    Stores data submitted at ANY station dynamically.
    No hardcoded vitals or lab buckets!
    """
    patient = models.ForeignKey(PatientWorkflow, on_delete=models.CASCADE, related_name='station_entries')
    station = models.ForeignKey(ScreeningStation, on_delete=models.PROTECT, related_name='entries')
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    # Entire dynamic payload captured based on the station's RoleConfig schema
    data = models.JSONField(default=dict, help_text="Data key-value pairs captured at this specific station")

    notes = models.TextField(blank=True, help_text="Optional comments or clinical observations")
    created_at = models.DateTimeField(auto_now_add=True)

    client_submission_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        db_index=True,
        help_text="Client-generated idempotency key for offline sync deduplication"
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = "Station Entry"
        verbose_name_plural = "Station Entries"
        indexes = [
            models.Index(fields=['station', 'created_at']),
            models.Index(fields=['patient', 'station']),
            models.Index(fields=['client_submission_id']),
        ]
        unique_together = [['patient', 'station', 'client_submission_id']]

    def __str__(self):
        return f"{self.patient.token_id} at {self.station.name}"