from django.contrib import admin
from .models import Screening, Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'specialization', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    list_filter = ['specialization', 'created_at']


@admin.register(Screening)
class ScreeningAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'age', 'gender', 'bmi', 'blood_pressure_status', 'glucose_status', 'has_consultation', 'created_at']
    search_fields = ['full_name', 'phone_number']
    list_filter = ['gender', 'created_at', 'doctor']
    readonly_fields = ['bmi', 'bmi_category', 'blood_pressure_status', 'glucose_status', 'is_critical', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'age', 'gender', 'phone_number', 'email')
        }),
        ('Physical Measurements', {
            'fields': ('weight_kg', 'height_cm', 'bmi', 'bmi_category')
        }),
        ('Vital Signs', {
            'fields': ('systolic_bp', 'diastolic_bp', 'blood_pressure_status', 'glucose_level', 'glucose_status', 'heart_rate')
        }),
        ('Medical History', {
            'fields': ('known_conditions', 'current_medications', 'notes')
        }),
        ('Screening Info', {
            'fields': ('screened_by', 'created_at')
        }),
        ('Doctor Consultation', {
            'fields': ('doctor', 'doctor_advice', 'consultation_date')
        }),
    )
