from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Screening, Doctor


class UserSerializer(serializers.ModelSerializer):
    """Serializer for Django's User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class DoctorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Doctor model.
    """
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Doctor
        fields = '__all__'
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class ScreeningSerializer(serializers.ModelSerializer):
    """
    Serializer for the Screening model.
    Includes computed properties as read-only fields for analytics.
    """
    # Computed properties for analytics
    bmi = serializers.ReadOnlyField()
    bmi_category = serializers.ReadOnlyField()
    blood_pressure_status = serializers.ReadOnlyField()
    glucose_status = serializers.ReadOnlyField()
    is_critical = serializers.ReadOnlyField()
    has_consultation = serializers.ReadOnlyField()
    
    # Nested doctor info (read-only for display)
    doctor_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Screening
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_doctor_info(self, obj):
        if obj.doctor:
            return {
                'name': f"Dr. {obj.doctor.user.get_full_name() or obj.doctor.user.username}",
                'date': obj.consultation_date
            }
        return None


class ScreeningCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating screenings (volunteer side).
    Omits doctor-specific fields that volunteers shouldn't modify.
    """
    class Meta:
        model = Screening
        exclude = ['doctor', 'doctor_advice', 'consultation_date']


class ScreeningConsultationSerializer(serializers.ModelSerializer):
    """
    Serializer for doctor's consultation.
    Only allows updating doctor-related fields.
    """
    class Meta:
        model = Screening
        fields = ['doctor', 'doctor_advice', 'requires_specialist_followup', 'consultation_date']
