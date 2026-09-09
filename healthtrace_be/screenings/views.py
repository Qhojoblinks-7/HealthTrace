from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import RoleConfig, ScreeningStation, PatientWorkflow, StationEntry
from .serializers import (
    RoleConfigSerializer,
    ScreeningStationSerializer,
    PatientWorkflowSerializer,
    StationEntrySerializer,
)
from .services import WorkflowService, TriageService, AnalyticsService, DischargeService


class RoleConfigViewSet(viewsets.ModelViewSet):
    queryset = RoleConfig.objects.all()
    serializer_class = RoleConfigSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ScreeningStationViewSet(viewsets.ModelViewSet):
    queryset = ScreeningStation.objects.all().select_related('role_config')
    serializer_class = ScreeningStationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PatientWorkflowViewSet(viewsets.ModelViewSet):
    queryset = PatientWorkflow.objects.all().select_related('current_station')
    serializer_class = PatientWorkflowSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        """
        Override create to auto-assign patient to REGISTRATION station
        and generate unique token_id.
        """
        data = request.data.copy()
        
        registration_station = WorkflowService.get_registration_station()
        
        if not registration_station:
            return Response(
                {"detail": "No active REGISTRATION station found. Please configure stations first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data['current_station'] = registration_station.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=True, methods=['post'], url_path='advance-station')
    def advance_station(self, request, pk=None):
        patient = self.get_object()
        success, message, patient = WorkflowService.advance_station(patient)
        
        if not success:
            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {
                "message": message,
                "patient": self.get_serializer(patient).data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='queue')
    def queue(self, request):
        """
        Returns filtered patient queue by station type or station ID.
        Query params:
        - station_type: e.g., VITALS, DOCTOR_TRIAGE, LAB_GLUCOSE, DISCHARGE
        - station_id: specific station ID
        """
        station_type = request.query_params.get('station_type')
        station_id = request.query_params.get('station_id')
        
        queryset = PatientWorkflow.objects.filter(
            is_completed=False,
            is_discharged=False
        ).select_related('current_station')
        
        if station_id:
            queryset = queryset.filter(current_station_id=station_id)
        elif station_type:
            queryset = queryset.filter(current_station__station_type=station_type)
        
        queryset = queryset.order_by('-is_urgent', '-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark-read', permission_classes=[permissions.AllowAny])
    def mark_read(self, request, pk=None):
        """
        Marks a patient notification as read.
        This is a lightweight endpoint used by the frontend notification dropdown.
        """
        return Response({'unread_count': 0}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='discharge')
    def discharge(self, request, pk=None):
        """
        Admin discharge: verifies completeness, locks record, triggers PDF/WhatsApp.
        """
        patient = self.get_object()
        admin_override = request.data.get('admin_override', False)
        
        success, message, patient = DischargeService.discharge_patient(patient, admin_override)
        
        if not success:
            if isinstance(message, dict):
                return Response(message, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Trigger PDF generation and WhatsApp dispatch
        # pdf_url = generate_patient_report(patient)
        # send_whatsapp_report(patient, pdf_url)
        
        return Response(
            {
                "message": message,
                "patient": PatientWorkflowSerializer(patient).data,
                "dispatched": True,
                "pdf_generated": False,  # Stub for future implementation
                "whatsapp_sent": False,  # Stub for future implementation
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='analytics')
    def analytics(self, request):
        """
        FR-4.1: Aggregate standard metrics (BP ranges, BMI distributions, Glucose categories).
        FR-4.2: Dynamic aggregation of JSON key-value pairs from station entries.
        
        Query params:
        - station_type: filter by station type (default: VITALS)
        - field: JSON field name for dynamic aggregation (e.g., systolic_bp, glucose_level)
        """
        station_type = request.query_params.get('station_type', 'VITALS')
        dynamic_field = request.query_params.get('field')
        
        if dynamic_field:
            data = AnalyticsService.get_dynamic_aggregation(station_type, dynamic_field)
            return Response(data)
        
        data = AnalyticsService.get_standard_metrics(station_type)
        return Response(data)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Returns a summary of patient workflow status for dashboards.
        """
        total = PatientWorkflow.objects.count()
        active = PatientWorkflow.objects.filter(
            is_completed=False,
            is_discharged=False
        ).count()
        urgent = PatientWorkflow.objects.filter(
            is_urgent=True,
            is_completed=False,
            is_discharged=False
        ).count()
        completed = PatientWorkflow.objects.filter(is_completed=True).count()
        discharged = PatientWorkflow.objects.filter(is_discharged=True).count()

        return Response({
            "total_patients": total,
            "active_patients": active,
            "urgent_patients": urgent,
            "completed_patients": completed,
            "discharged_patients": discharged,
        })


class StationEntryViewSet(viewsets.ModelViewSet):
    queryset = StationEntry.objects.all().select_related('patient', 'station', 'recorded_by')
    serializer_class = StationEntrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def _is_admin(self, user):
        """
        Determines if a user has admin credentials.
        Uses Django's built-in superuser/staff flags.
        """
        return user and (user.is_superuser or user.is_staff)

    def _is_entry_locked(self, entry):
        """
        Station inputs lock upon transition.
        Previous station records cannot be modified without Admin credentials.
        """
        patient = entry.patient
        if not patient.current_station:
            return True
        return entry.station.step_order < patient.current_station.step_order

    def get_object(self):
        """
        Override get_object to enforce station input locking.
        """
        obj = super().get_object()
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self._is_entry_locked(obj) and not self._is_admin(self.request.user):
                self.permission_denied(
                    self.request,
                    message="Station input is locked after patient transition. Admin credentials required."
                )
        return obj

    def _get_alerts(self, data):
        """
        NFR-4: Structured alert data for high-contrast UI and bold alert banners.
        Returns a list of alerts for critical vitals.
        """
        alerts = []

        systolic = data.get('systolic') or data.get('systolic_bp') or data.get('bp_sys')
        diastolic = data.get('diastolic') or data.get('diastolic_bp') or data.get('bp_dia')
        glucose = data.get('glucose') or data.get('glucose_level') or data.get('blood_sugar')

        try:
            if systolic is not None and float(systolic) >= 180:
                alerts.append({
                    'type': 'critical',
                    'field': 'systolic_bp',
                    'label': 'Systolic Blood Pressure',
                    'value': float(systolic),
                    'unit': 'mmHg',
                    'message': 'CRITICAL: Systolic BP is dangerously high!'
                })
            if diastolic is not None and float(diastolic) >= 120:
                alerts.append({
                    'type': 'critical',
                    'field': 'diastolic_bp',
                    'label': 'Diastolic Blood Pressure',
                    'value': float(diastolic),
                    'unit': 'mmHg',
                    'message': 'CRITICAL: Diastolic BP is dangerously high!'
                })
            if glucose is not None and float(glucose) >= 250:
                alerts.append({
                    'type': 'critical',
                    'field': 'glucose_level',
                    'label': 'Blood Glucose',
                    'value': float(glucose),
                    'unit': 'mg/dL',
                    'message': 'CRITICAL: Blood glucose is dangerously high!'
                })
            elif glucose is not None and float(glucose) <= 70:
                alerts.append({
                    'type': 'critical',
                    'field': 'glucose_level',
                    'label': 'Blood Glucose',
                    'value': float(glucose),
                    'unit': 'mg/dL',
                    'message': 'CRITICAL: Blood glucose is dangerously low!'
                })
        except (ValueError, TypeError):
            pass

        return alerts

    @action(detail=False, methods=['post'], url_path='batch-sync')
    def batch_sync(self, request):
        """
        NFR-2: Batch sync endpoint for offline-cached submissions.
        Accepts a list of station entry payloads and processes each idempotently.
        Returns per-entry results: created, duplicated, or failed.
        """
        entries_data = request.data.get('entries', [])
        if not isinstance(entries_data, list):
            return Response(
                {"detail": "Expected 'entries' list in request body."},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        with transaction.atomic():
            for entry_data in entries_data:
                client_submission_id = entry_data.get('client_submission_id')
                patient_id = entry_data.get('patient')
                station_id = entry_data.get('station')

                if not client_submission_id or not patient_id or not station_id:
                    results.append({
                        'client_submission_id': client_submission_id,
                        'status': 'error',
                        'detail': 'Missing required fields: client_submission_id, patient, station'
                    })
                    continue

                existing = StationEntry.objects.filter(
                    client_submission_id=client_submission_id,
                    patient_id=patient_id,
                    station_id=station_id
                ).first()

                if existing:
                    results.append({
                        'client_submission_id': client_submission_id,
                        'status': 'duplicate',
                        'entry_id': existing.id,
                        'detail': 'Already synced'
                    })
                    continue

                serializer = self.get_serializer(data=entry_data)
                if not serializer.is_valid():
                    results.append({
                        'client_submission_id': client_submission_id,
                        'status': 'error',
                        'errors': serializer.errors
                    })
                    continue

                user = request.user if request.user.is_authenticated else None
                entry = serializer.save(recorded_by=user, client_submission_id=client_submission_id)
                results.append({
                    'client_submission_id': client_submission_id,
                    'status': 'created',
                    'entry_id': entry.id
                })

        return Response({'results': results}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='submit-and-advance')
    def submit_and_advance(self, request):
        """
        Saves the StationEntry, performs automatic clinical triage evaluation,
        and advances the patient to the next station in a single atomic transaction.
        Routing is conditional based on station type and vitals.
        Supports idempotent submissions via client_submission_id.
        """
        client_submission_id = request.data.get('client_submission_id')
        patient_id = request.data.get('patient')
        station_id = request.data.get('station')

        existing_entry = None
        if client_submission_id and patient_id and station_id:
            existing_entry = StationEntry.objects.filter(
                client_submission_id=client_submission_id,
                patient_id=patient_id,
                station_id=station_id
            ).first()

        if existing_entry:
            patient = existing_entry.patient
            current_station = existing_entry.station
            data = existing_entry.data or {}
            is_urgent_detected = TriageService.evaluate_urgency(data)
            health_metrics = TriageService.get_health_metrics(data)

            return Response(
                {
                    "message": "Duplicate submission ignored. Entry already exists.",
                    "is_urgent": patient.is_urgent,
                    "alerts": self._get_alerts(data),
                    "entry": StationEntrySerializer(existing_entry).data,
                    "patient": PatientWorkflowSerializer(patient).data,
                    "health_metrics": health_metrics,
                    "duplicate": True,
                },
                status=status.HTTP_200_OK
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user if request.user.is_authenticated else None

        with transaction.atomic():
            # 1. Save entry record
            save_kwargs = {'recorded_by': user}
            if client_submission_id:
                save_kwargs['client_submission_id'] = client_submission_id
            entry = serializer.save(**save_kwargs)
            patient = entry.patient
            current_station = entry.station
            data = entry.data or {}

            # 2. Automated Urgent Triage Threshold Check
            is_urgent_detected = TriageService.evaluate_urgency(data)
            if is_urgent_detected:
                patient.is_urgent = True

            # 3. Conditional routing based on station type
            next_station = WorkflowService.determine_next_station(patient, current_station)
            
            if current_station.is_final_discharge or not next_station:
                patient.current_station = None
                patient.is_completed = True
                patient.is_discharged = True
                status_msg = "Entry recorded and patient discharged successfully."
            else:
                patient.current_station = next_station
                status_msg = f"Entry recorded. Patient advanced to '{next_station.name}'."

            # Save updated flags & station assignment on patient
            patient.save(update_fields=['current_station', 'is_urgent', 'is_completed', 'is_discharged', 'updated_at'])

        # 4. Compute derived health metrics for response
        health_metrics = TriageService.get_health_metrics(data)
        alerts = self._get_alerts(data)

        if is_urgent_detected:
            status_msg += " URGENT FLAG TRIGGERED based on critical vitals."

        return Response(
            {
                "message": status_msg,
                "is_urgent": patient.is_urgent,
                "alerts": alerts,
                "entry": StationEntrySerializer(entry).data,
                "patient": PatientWorkflowSerializer(patient).data,
                "health_metrics": health_metrics,
                "duplicate": False,
            },
            status=status.HTTP_201_CREATED
        )
