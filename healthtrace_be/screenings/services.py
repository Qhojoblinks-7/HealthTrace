from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q

from .models import RoleConfig, ScreeningStation, PatientWorkflow, StationEntry
from .health_utils import (
    calculate_bmi,
    get_bmi_category,
    get_blood_pressure_status,
    get_glucose_status,
    evaluate_clinical_urgency,
)


CACHE_TIMEOUT = 60


class WorkflowService:
    """
    Handles patient workflow routing and station advancement logic.
    Separation of concern: business rules for moving patients through stations.
    """

    @staticmethod
    def get_registration_station():
        cache_key = 'registration_station'
        station = cache.get(cache_key)
        if station is None:
            station = ScreeningStation.objects.filter(
                station_type='REGISTRATION',
                is_active=True
            ).order_by('step_order').first()
            cache.set(cache_key, station, CACHE_TIMEOUT)
        return station

    @staticmethod
    def get_active_stations():
        cache_key = 'active_stations'
        stations = cache.get(cache_key)
        if stations is None:
            stations = list(ScreeningStation.objects.filter(is_active=True).order_by('step_order'))
            cache.set(cache_key, stations, CACHE_TIMEOUT)
        return stations

    @staticmethod
    def invalidate_station_cache():
        cache.delete('registration_station')
        cache.delete('active_stations')

    @staticmethod
    def determine_next_station(patient, current_station):
        """
        Conditional routing logic based on current station type and submitted data.
        - REGISTRATION -> VITALS
        - VITALS -> DOCTOR_TRIAGE or LAB_GLUCOSE based on urgency, or DISCHARGE if normal
        - DOCTOR_TRIAGE/LAB_GLUCOSE -> DISCHARGE or next station
        - DISCHARGE -> None (workflow complete)
        """
        active_stations = WorkflowService.get_active_stations()
        current_type = current_station.station_type

        if current_type == 'REGISTRATION':
            for station in active_stations:
                if station.station_type == 'VITALS':
                    return station
            return None

        elif current_type == 'VITALS':
            if patient.is_urgent:
                for station in active_stations:
                    if station.station_type == 'DOCTOR_TRIAGE':
                        return station
                return None
            else:
                for station in active_stations:
                    if station.is_final_discharge:
                        return station
                for station in active_stations:
                    if station.station_type == 'GENERAL':
                        return station
                return None

        elif current_type in ['DOCTOR_TRIAGE', 'LAB_GLUCOSE']:
            for station in active_stations:
                if station.is_final_discharge:
                    return station
            for station in active_stations:
                if station.step_order > current_station.step_order:
                    return station
            return None

        elif current_type == 'DISCHARGE' or current_station.is_final_discharge:
            return None

        for station in active_stations:
            if station.step_order > current_station.step_order:
                return station
        return None

    @staticmethod
    def advance_station(patient):
        """
        Advances patient to next station or completes workflow.
        Returns (success, message, patient)
        """
        if patient.is_completed or patient.is_discharged:
            return False, "Patient has already completed or been discharged.", patient

        active_stations = WorkflowService.get_active_stations()
        if not active_stations:
            return False, "No active screening stations found in system configuration.", patient

        if not patient.current_station:
            next_station = active_stations[0]
            patient.current_station = next_station
            patient.save(update_fields=['current_station', 'updated_at'])
            return True, f"Patient assigned to initial station: {next_station.name}", patient

        current = patient.current_station

        if current.is_final_discharge:
            patient.current_station = None
            patient.is_completed = True
            patient.is_discharged = True
            patient.save(update_fields=['current_station', 'is_completed', 'is_discharged', 'updated_at'])
            return True, "Patient discharged successfully. Workflow marked as completed and locked.", patient

        next_station = None
        for station in active_stations:
            if station.step_order > current.step_order:
                next_station = station
                break

        if next_station:
            patient.current_station = next_station
            patient.save(update_fields=['current_station', 'updated_at'])
            return True, f"Patient advanced from '{current.name}' to '{next_station.name}'", patient
        else:
            patient.current_station = None
            patient.is_completed = True
            patient.is_discharged = True
            patient.save(update_fields=['current_station', 'is_completed', 'is_discharged', 'updated_at'])
            return True, "Patient reached end of active stations. Workflow completed and locked.", patient


class TriageService:
    """
    Handles clinical triage evaluation and urgency detection.
    Separation of concern: medical logic separate from workflow and presentation.
    """

    @staticmethod
    def evaluate_urgency(data):
        return evaluate_clinical_urgency(data)

    @staticmethod
    def get_health_metrics(data):
        """
        Computes BMI, BP status, and glucose status from raw station data.
        Returns a dict suitable for API responses.
        """
        weight_kg = data.get('weight_kg') or data.get('weight')
        height_cm = data.get('height_cm') or data.get('height')
        systolic = data.get('systolic') or data.get('systolic_bp') or data.get('bp_sys')
        diastolic = data.get('diastolic') or data.get('diastolic_bp') or data.get('bp_dia')
        glucose = data.get('glucose') or data.get('glucose_level') or data.get('blood_sugar')

        bmi = calculate_bmi(weight_kg, height_cm) if weight_kg and height_cm else None
        bmi_category = get_bmi_category(bmi) if bmi is not None else None
        bp_status = get_blood_pressure_status(systolic, diastolic) if systolic and diastolic else None
        glucose_status = get_glucose_status(glucose) if glucose is not None else None

        return {
            "bmi": bmi,
            "bmi_category": bmi_category,
            "blood_pressure_status": bp_status,
            "glucose_status": glucose_status,
        }


class AnalyticsService:
    """
    Handles aggregation logic for reporting and dashboards.
    Separation of concern: read-only analytical queries.
    """

    @staticmethod
    def get_standard_metrics(station_type='VITALS'):
        """
        FR-4.1: Aggregate standard metrics (BP ranges, BMI distributions, Glucose categories).
        """
        entries = StationEntry.objects.filter(
            station__station_type=station_type,
            station__is_active=True
        ).select_related('station', 'patient')

        bp_distribution = {
            "Normal": 0,
            "Elevated": 0,
            "Stage 1": 0,
            "Stage 2": 0,
            "Crisis": 0,
            "Unknown": 0,
        }
        bmi_distribution = {
            "Underweight": 0,
            "Normal": 0,
            "Overweight": 0,
            "Obese": 0,
            "Unknown": 0,
        }
        glucose_distribution = {
            "Normal": 0,
            "Prediabetes": 0,
            "Diabetes": 0,
            "Unknown": 0,
        }

        urgent_count = 0
        total_count = 0

        for entry in entries:
            total_count += 1
            data = entry.data or {}

            # BP categorization
            systolic = data.get('systolic') or data.get('systolic_bp') or data.get('bp_sys')
            diastolic = data.get('diastolic') or data.get('diastolic_bp') or data.get('bp_dia')
            if systolic and diastolic:
                bp_status = get_blood_pressure_status(systolic, diastolic)
                if bp_status and bp_status in bp_distribution:
                    bp_distribution[bp_status] += 1
                else:
                    bp_distribution["Unknown"] += 1
            else:
                bp_distribution["Unknown"] += 1

            # BMI categorization
            weight = data.get('weight_kg') or data.get('weight')
            height = data.get('height_cm') or data.get('height')
            if weight and height:
                bmi = calculate_bmi(weight, height)
                bmi_cat = get_bmi_category(bmi)
                if bmi_cat and bmi_cat in bmi_distribution:
                    bmi_distribution[bmi_cat] += 1
                else:
                    bmi_distribution["Unknown"] += 1
            else:
                bmi_distribution["Unknown"] += 1

            # Glucose categorization
            glucose = data.get('glucose') or data.get('glucose_level') or data.get('blood_sugar')
            if glucose is not None:
                glucose_status = get_glucose_status(glucose)
                if glucose_status and glucose_status in glucose_distribution:
                    glucose_distribution[glucose_status] += 1
                else:
                    glucose_distribution["Unknown"] += 1
            else:
                glucose_distribution["Unknown"] += 1

            # Urgent count
            if evaluate_clinical_urgency(data):
                urgent_count += 1

        return {
            "station_type": station_type,
            "total_entries": total_count,
            "urgent_count": urgent_count,
            "blood_pressure_distribution": bp_distribution,
            "bmi_distribution": bmi_distribution,
            "glucose_distribution": glucose_distribution,
        }

    @staticmethod
    def get_dynamic_aggregation(station_type='VITALS', field=None):
        """
        FR-4.2: Aggregate key-value pairs from custom_data JSON.
        If field is provided, aggregates counts for that specific field.
        Otherwise returns full custom_data aggregation.
        """
        entries = StationEntry.objects.filter(
            station__station_type=station_type,
            station__is_active=True
        ).select_related('station', 'patient')

        if field:
            aggregation = {}
            for entry in entries:
                value = entry.data.get(field)
                if value is not None:
                    key = str(value)
                    aggregation[key] = aggregation.get(key, 0) + 1

            return {
                "station_type": station_type,
                "field": field,
                "aggregation": aggregation,
                "total_entries": entries.count(),
            }

        # Full custom_data aggregation
        aggregation = {}
        for entry in entries:
            for key, value in (entry.data or {}).items():
                agg_key = f"{key}:{value}"
                aggregation[agg_key] = aggregation.get(agg_key, 0) + 1

        return {
            "station_type": station_type,
            "aggregation": aggregation,
            "total_entries": entries.count(),
        }


class DischargeService:
    """
    Handles admin discharge logic, record locking, and completeness checks.
    Separation of concern: discharge-specific business rules.
    """

    @staticmethod
    def check_completeness(patient):
        """
        Checks if patient has completed all active stations.
        Returns (is_complete, missing_stations)
        """
        active_stations = WorkflowService.get_active_stations()
        active_station_ids = [s.id for s in active_stations]

        completed_station_ids = set(
            patient.station_entries.filter(station_id__in=active_station_ids)
            .values_list('station_id', flat=True)
            .distinct()
        )

        missing_stations = []
        for station in active_stations:
            if station.id not in completed_station_ids:
                missing_stations.append(station.name)

        return len(missing_stations) == 0, missing_stations

    @staticmethod
    def discharge_patient(patient, admin_override=False):
        """
        Performs discharge with optional admin override.
        Returns (success, message, patient)
        """
        if patient.is_discharged or patient.is_completed:
            return False, "Patient has already been discharged.", patient

        is_complete, missing_stations = DischargeService.check_completeness(patient)

        if not is_complete and not admin_override:
            return False, {
                "detail": "Patient has not completed all stations.",
                "missing_stations": missing_stations,
                "message": "Set admin_override=true to force discharge."
            }, patient

        # Lock and discharge
        patient.current_station = None
        patient.is_completed = True
        patient.is_discharged = True
        patient.save(update_fields=['current_station', 'is_completed', 'is_discharged', 'updated_at'])

        return True, "Patient discharged successfully. Record locked.", patient
