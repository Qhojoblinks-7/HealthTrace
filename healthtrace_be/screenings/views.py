from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Avg, Q, F, ExpressionWrapper
from django.db.models import DecimalField as DBDecimalField
from datetime import datetime
from django.utils import timezone
from .models import Screening, Doctor
from .serializers import (
    ScreeningSerializer, 
    ScreeningCreateSerializer,
    ScreeningConsultationSerializer,
    DoctorSerializer
)


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Doctor model.
    Allows doctors to be listed, created, and retrieved.
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Doctors can list other doctors
        return Doctor.objects.all()


class ScreeningViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Screening model.
    Provides full CRUD operations with different serializers for different actions.
    """
    queryset = Screening.objects.all().order_by('-created_at')
    permission_classes = [AllowAny]  # Open access for community outreach
    pagination_class = PageNumberPagination
    page_size = 20
    
    def get_serializer_class(self):
        """Return different serializers based on the action."""
        if self.action == 'create':
            return ScreeningCreateSerializer
        elif self.action == 'consult':
            return ScreeningConsultationSerializer
        return ScreeningSerializer
    
    def get_queryset(self):
        """Filter screenings based on query parameters."""
        queryset = super().get_queryset()
        
        # Search by name or phone
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) | 
                Q(phone_number__icontains=search)
            )
        
        # Filter by consultation status
        has_consultation = self.request.query_params.get('consultation', None)
        if has_consultation == 'true':
            queryset = queryset.filter(doctor__isnull=False)
        elif has_consultation == 'false':
            queryset = queryset.filter(doctor__isnull=True)
        
        # Filter by critical status - use database-level filtering for efficiency
        critical = self.request.query_params.get('critical', None)
        if critical == 'true':
            queryset = queryset.filter(
                Q(systolic_bp__gt=180) | 
                Q(diastolic_bp__gt=120) | 
                Q(glucose_level__gt=600)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def consult(self, request, pk=None):
        """
        Doctor consultation endpoint.
        Allows doctor to add advice to a screening.
        """
        screening = self.get_object()
        serializer = ScreeningConsultationSerializer(
            screening, 
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            # Try to get the doctor from the authenticated user
            doctor = None
            if request.user.is_authenticated and hasattr(request.user, 'doctor_profile'):
                doctor = request.user.doctor_profile
            # If no authenticated doctor, try to get from request data or use first available
            elif request.data.get('doctor_id'):
                from .models import Doctor
                try:
                    doctor = Doctor.objects.get(id=request.data.get('doctor_id'))
                except Doctor.DoesNotExist:
                    pass
            # Fallback: get or create a default doctor for demo purposes
            if not doctor:
                from .models import Doctor
                from django.contrib.auth.models import User
                try:
                    # Try to get existing default doctor
                    doctor = Doctor.objects.first()
                    if not doctor:
                        # Create a default user and doctor for demo
                        user, _ = User.objects.get_or_create(
                            username='demo_doctor',
                            defaults={'first_name': 'Demo', 'last_name': 'Doctor'}
                        )
                        doctor, _ = Doctor.objects.get_or_create(
                            user=user,
                            defaults={'specialization': 'General Practitioner'}
                        )
                except Exception:
                    pass
            
            # Save with consultation date and doctor
            serializer.save(consultation_date=timezone.now(), doctor=doctor)
            
            # Refresh the screening object to get updated data
            screening.refresh_from_db()
            
            # Return full screening data using ScreeningSerializer
            full_serializer = ScreeningSerializer(screening)
            return Response(full_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Returns quick stats for volunteers:
        - total_screened: Total number of people screened
        - today_count: Number of screenings today
        - pending_consultations: Screenings without doctor advice
        - critical_cases: High-risk patients needing immediate attention
        """
        queryset = self.get_queryset()
        
        # Get today's date
        today = datetime.now().date()
        
        # Calculate stats
        total_screened = queryset.count()
        today_count = queryset.filter(created_at__date=today).count()
        pending_count = queryset.filter(doctor__isnull=True).count()
        
        # Calculate average BMI using database aggregation for efficiency
        screenings_with_bmi = queryset.exclude(
            weight_kg__isnull=True, 
            height_cm__isnull=True
        ).annotate(
            bmi_calc=ExpressionWrapper(
                F('weight_kg') / ((F('height_cm') / 100) ** 2),
                output_field=DBDecimalField(max_digits=4, decimal_places=2)
            )
        )
        avg_bmi_result = screenings_with_bmi.aggregate(Avg('bmi_calc'))
        avg_bmi = round(avg_bmi_result['bmi_calc__avg'], 1) if avg_bmi_result['bmi_calc__avg'] else 0
        
        # Count high-risk conditions
        high_bp_count = queryset.filter(
            Q(systolic_bp__gte=140) | Q(diastolic_bp__gte=90)
        ).count()
        
        high_glucose_count = queryset.filter(
            glucose_level__gte=200
        ).count()
        
        # Critical cases - use database filtering for efficiency
        critical_count = queryset.filter(
            Q(systolic_bp__gt=180) | 
            Q(diastolic_bp__gt=120) | 
            Q(glucose_level__gt=400)
        ).count()
        
        return Response({
            'total_screened': total_screened,
            'today_count': today_count,
            'pending_consultations': pending_count,
            'avg_bmi': avg_bmi,
            'high_bp_count': high_bp_count,
            'high_glucose_count': high_glucose_count,
            'critical_cases': critical_count,
        })
    
    @action(detail=False, methods=['get'])
    def notifications(self, request):
        """
        Returns notifications for the doctor dashboard.
        """
        queryset = self.get_queryset()
        today = datetime.now().date()
        
        notifications = []
        
        # Get critical cases (today) - these will be shown first
        critical_cases = queryset.filter(
            Q(systolic_bp__gt=180) | 
            Q(diastolic_bp__gt=120) | 
            Q(glucose_level__gt=400),
            created_at__date=today
        )[:30]
        
        for case in critical_cases:
            notifications.append({
                'id': f'critical_{case.id}',
                'type': 'critical',
                'title': 'Critical Patient',
                'message': f'{case.full_name} has critical vital signs',
                'patient_id': case.id,
                'timestamp': case.created_at.isoformat(),
                'read': case.has_consultation,
                'priority': 1,  # High priority
            })
        
        # Get pending consultations (today) - these will be shown after critical
        pending_cases = queryset.filter(
            doctor__isnull=True,
            created_at__date=today
        )[:30]
        
        for case in pending_cases:
            notifications.append({
                'id': f'pending_{case.id}',
                'type': 'warning',
                'title': 'Pending Consultation',
                'message': f'{case.full_name} is waiting for consultation',
                'patient_id': case.id,
                'timestamp': case.created_at.isoformat(),
                'read': case.has_consultation,
                'priority': 2,  # Lower priority
            })
        
        # Sort by priority (critical first), then by timestamp (newest first)
        notifications.sort(key=lambda x: (x['priority'], x['timestamp']), reverse=True)
        
        # Get actual counts for badge
        total_critical = queryset.filter(
            Q(systolic_bp__gt=180) | 
            Q(diastolic_bp__gt=120) | 
            Q(glucose_level__gt=400),
            created_at__date=today
        ).count()
        
        total_pending = queryset.filter(
            doctor__isnull=True,
            created_at__date=today
        ).count()
        
        return Response({
            'notifications': notifications,
            'unread_count': total_critical + total_pending,
        })
    
    @action(detail=False, methods=['post'])
    def mark_notification_read(self, request):
        """
        Mark a notification as read by updating the screening's consultation status.
        """
        patient_id = request.data.get('patient_id')
        
        if not patient_id:
            return Response(
                {'error': 'patient_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            screening = Screening.objects.get(id=patient_id)
            
            # Get today's counts for unread
            today = timezone.now().date()
            total_critical = Screening.objects.filter(
                Q(systolic_bp__gt=180) | 
                Q(diastolic_bp__gt=120) | 
                Q(glucose_level__gt=400),
                created_at__date=today
            ).count()
            
            total_pending = Screening.objects.filter(
                doctor__isnull=True,
                created_at__date=today
            ).count()
            
            return Response({
                'success': True,
                'patient_id': patient_id,
                'read': screening.has_consultation,
                'unread_count': total_critical + total_pending
            })
        except Screening.DoesNotExist:
            return Response(
                {'error': 'Patient not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Community health analytics for the doctor's report.
        """
        queryset = self.get_queryset()
        
        # Total count
        total = queryset.count()
        
        # Age distribution
        age_groups = {
            '0-17': queryset.filter(age__lt=18).count(),
            '18-30': queryset.filter(age__gte=18, age__lt=30).count(),
            '31-45': queryset.filter(age__gte=31, age__lt=45).count(),
            '46-60': queryset.filter(age__gte=46, age__lt=60).count(),
            '60+': queryset.filter(age__gte=60).count(),
        }
        
        # Health conditions prevalence
        bp_prevalence = queryset.filter(
            Q(systolic_bp__gte=140) | Q(diastolic_bp__gte=90)
        ).count()
        
        glucose_prevalence = queryset.filter(
            glucose_level__gte=200
        ).count()
        
        bmi_obese = queryset.filter(
            weight_kg__isnull=False, 
            height_cm__isnull=False
        ).annotate(
            bmi_calc=ExpressionWrapper(
                F('weight_kg') / ((F('height_cm') / 100) ** 2),
                output_field=DBDecimalField(max_digits=5, decimal_places=2)
            )
        ).filter(bmi_calc__gte=30).count()
        
        # Consultations completed
        consultations = queryset.filter(doctor__isnull=False).count()
        
        return Response({
            'total_screened': total,
            'age_distribution': age_groups,
            'hypertension_prevalence': {
                'count': bp_prevalence,
                'percentage': round(bp_prevalence / total * 100, 1) if total > 0 else 0
            },
            'diabetes_prevalence': {
                'count': glucose_prevalence,
                'percentage': round(glucose_prevalence / total * 100, 1) if total > 0 else 0
            },
            'consultations_completed': consultations,
        })
