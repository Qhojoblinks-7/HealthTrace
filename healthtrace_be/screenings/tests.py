from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .health_utils import (
    calculate_bmi,
    get_bmi_category,
    get_blood_pressure_status,
    get_glucose_status,
    evaluate_clinical_urgency,
)
from .models import RoleConfig, ScreeningStation, PatientWorkflow, StationEntry


class CalculateBMITests(TestCase):
    def test_bmi_normal(self):
        self.assertEqual(calculate_bmi(70, 175), 22.9)

    def test_bmi_underweight(self):
        self.assertEqual(calculate_bmi(50, 175), 16.3)

    def test_bmi_overweight(self):
        self.assertEqual(calculate_bmi(80, 175), 26.1)

    def test_bmi_obese(self):
        self.assertEqual(calculate_bmi(100, 175), 32.7)

    def test_bmi_zero_weight(self):
        self.assertIsNone(calculate_bmi(0, 175))

    def test_bmi_zero_height(self):
        self.assertIsNone(calculate_bmi(70, 0))

    def test_bmi_invalid_input(self):
        self.assertIsNone(calculate_bmi("abc", 175))


class GetBMICategoryTests(TestCase):
    def test_underweight(self):
        self.assertEqual(get_bmi_category(18.4), 'Underweight')

    def test_normal(self):
        self.assertEqual(get_bmi_category(22.0), 'Normal')

    def test_overweight(self):
        self.assertEqual(get_bmi_category(27.0), 'Overweight')

    def test_obese(self):
        self.assertEqual(get_bmi_category(32.0), 'Obese')

    def test_none(self):
        self.assertIsNone(get_bmi_category(None))


class GetBloodPressureStatusTests(TestCase):
    def test_normal(self):
        self.assertEqual(get_blood_pressure_status(118, 75), 'Normal')

    def test_elevated(self):
        self.assertEqual(get_blood_pressure_status(125, 75), 'Elevated')

    def test_stage_1(self):
        self.assertEqual(get_blood_pressure_status(135, 85), 'Stage 1')

    def test_stage_2_systolic(self):
        self.assertEqual(get_blood_pressure_status(145, 80), 'Stage 2')

    def test_stage_2_diastolic(self):
        self.assertEqual(get_blood_pressure_status(130, 92), 'Stage 2')

    def test_crisis_systolic(self):
        self.assertEqual(get_blood_pressure_status(185, 80), 'Crisis')

    def test_crisis_diastolic(self):
        self.assertEqual(get_blood_pressure_status(130, 125), 'Crisis')

    def test_invalid_input(self):
        self.assertIsNone(get_blood_pressure_status("abc", 80))


class GetGlucoseStatusTests(TestCase):
    def test_normal(self):
        self.assertEqual(get_glucose_status(110), 'Normal')

    def test_prediabetes_lower(self):
        self.assertEqual(get_glucose_status(140), 'Prediabetes')

    def test_prediabetes_upper(self):
        self.assertEqual(get_glucose_status(199), 'Prediabetes')

    def test_diabetes(self):
        self.assertEqual(get_glucose_status(250), 'Diabetes')

    def test_invalid_input(self):
        self.assertIsNone(get_glucose_status("abc"))


class EvaluateClinicalUrgencyTests(TestCase):
    def test_systolic_crisis(self):
        self.assertTrue(evaluate_clinical_urgency({'systolic': 185}))

    def test_diastolic_crisis(self):
        self.assertTrue(evaluate_clinical_urgency({'diastolic': 125}))

    def test_glucose_hyper(self):
        self.assertTrue(evaluate_clinical_urgency({'glucose': 260}))

    def test_glucose_hypo(self):
        self.assertTrue(evaluate_clinical_urgency({'glucose': 65}))

    def test_glucose_normal(self):
        self.assertFalse(evaluate_clinical_urgency({'glucose': 120}))

    def test_bp_normal(self):
        self.assertFalse(evaluate_clinical_urgency({'systolic': 120, 'diastolic': 80}))

    def test_glucose_threshold_250(self):
        self.assertFalse(evaluate_clinical_urgency({'glucose': 249}))

    def test_glucose_threshold_250_met(self):
        self.assertTrue(evaluate_clinical_urgency({'glucose': 250}))

    def test_alternate_keys(self):
        self.assertTrue(evaluate_clinical_urgency({'systolic_bp': 190, 'bp_dia': 125, 'blood_sugar': 260}))

    def test_empty_data(self):
        self.assertFalse(evaluate_clinical_urgency({}))


class FR3WorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create role configs
        self.reg_role = RoleConfig.objects.create(
            role_name='Registration',
            schema=[{'name': 'full_name', 'type': 'text', 'required': True}]
        )
        self.vitals_role = RoleConfig.objects.create(
            role_name='Vitals',
            schema=[
                {'name': 'systolic_bp', 'type': 'number', 'required': True},
                {'name': 'diastolic_bp', 'type': 'number', 'required': True},
                {'name': 'glucose_level', 'type': 'number', 'required': True},
            ]
        )
        self.doctor_role = RoleConfig.objects.create(
            role_name='Doctor Consultation',
            schema=[{'name': 'consultation_notes', 'type': 'text', 'required': False}]
        )
        
        # Create stations
        self.reg_station = ScreeningStation.objects.create(
            name='Table 1: Registration',
            step_order=1,
            station_type='REGISTRATION',
            role_config=self.reg_role,
            is_active=True
        )
        self.vitals_station = ScreeningStation.objects.create(
            name='Table 2: Vitals',
            step_order=2,
            station_type='VITALS',
            role_config=self.vitals_role,
            is_active=True
        )
        self.doctor_station = ScreeningStation.objects.create(
            name='Table 3: Doctor',
            step_order=3,
            station_type='DOCTOR_TRIAGE',
            role_config=self.doctor_role,
            is_active=True
        )
        self.discharge_station = ScreeningStation.objects.create(
            name='Table 4: Discharge',
            step_order=4,
            station_type='DISCHARGE',
            role_config=self.doctor_role,
            is_final_discharge=True,
            is_active=True
        )

    def test_token_generated_on_create(self):
        response = self.client.post('/api/patients/', {'patient_name': 'John Doe'})
        self.assertEqual(response.status_code, 201)
        self.assertIn('token_id', response.data)
        self.assertTrue(response.data['token_id'].startswith('#'))
        self.assertEqual(response.data['current_station'], self.reg_station.id)

    def test_dynamic_station_creation_via_api(self):
        new_station_data = {
            'name': 'Table 5: Optometry',
            'step_order': 5,
            'station_type': 'GENERAL',
            'role_config': self.reg_role.id,
            'is_active': True
        }
        response = self.client.post('/api/stations/', new_station_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Table 5: Optometry')
        self.assertEqual(response.data['station_type'], 'GENERAL')

    def test_queue_endpoint_filters_by_station_type(self):
        patient = PatientWorkflow.objects.create(
            token_id='#A-101',
            patient_name='Jane Doe',
            current_station=self.vitals_station
        )
        
        response = self.client.get('/api/patients/queue/', {'station_type': 'VITALS'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['token_id'], '#A-101')

    def test_discharge_locks_record(self):
        patient = PatientWorkflow.objects.create(
            token_id='#A-102',
            patient_name='Bob Smith',
            current_station=self.discharge_station
        )
        
        # Create entries for all stations including discharge
        StationEntry.objects.create(patient=patient, station=self.reg_station, data={}, client_submission_id='e1')
        StationEntry.objects.create(patient=patient, station=self.vitals_station, data={}, client_submission_id='e2')
        StationEntry.objects.create(patient=patient, station=self.doctor_station, data={}, client_submission_id='e3')
        StationEntry.objects.create(patient=patient, station=self.discharge_station, data={}, client_submission_id='e4')
        
        response = self.client.post(f'/api/patients/{patient.id}/discharge/')
        self.assertEqual(response.status_code, 200)
        patient.refresh_from_db()
        self.assertTrue(patient.is_discharged)
        self.assertTrue(patient.is_completed)
        self.assertIsNone(patient.current_station)

    def test_discharge_requires_completion_or_override(self):
        patient = PatientWorkflow.objects.create(
            token_id='#A-103',
            patient_name='Alice Brown',
            current_station=self.vitals_station
        )
        
        response = self.client.post(f'/api/patients/{patient.id}/discharge/')
        self.assertEqual(response.status_code, 400)
        self.assertIn('missing_stations', response.data)
        
        # With admin override
        response = self.client.post(
            f'/api/patients/{patient.id}/discharge/',
            {'admin_override': True}
        )
        self.assertEqual(response.status_code, 200)
        patient.refresh_from_db()
        self.assertTrue(patient.is_discharged)

    def test_submit_and_advance_routes_critical_to_doctor(self):
        patient = PatientWorkflow.objects.create(
            token_id='#A-104',
            patient_name='Critical Patient',
            current_station=self.vitals_station
        )
        
        entry_data = {
            'patient': patient.id,
            'station': self.vitals_station.id,
            'data': {
                'systolic_bp': 190,
                'diastolic_bp': 125,
                'glucose_level': 300,
                'weight_kg': 80,
                'height_cm': 175
            }
        }
        
        response = self.client.post('/api/entries/submit-and-advance/', entry_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['is_urgent'])
        patient.refresh_from_db()
        self.assertEqual(patient.current_station, self.doctor_station)

    def test_submit_and_advance_routes_normal_to_discharge(self):
        patient = PatientWorkflow.objects.create(
            token_id='#A-105',
            patient_name='Normal Patient',
            current_station=self.vitals_station
        )
        
        entry_data = {
            'patient': patient.id,
            'station': self.vitals_station.id,
            'data': {
                'systolic_bp': 118,
                'diastolic_bp': 75,
                'glucose_level': 100,
                'weight_kg': 70,
                'height_cm': 175
            }
        }
        
        response = self.client.post('/api/entries/submit-and-advance/', entry_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data['is_urgent'])
        patient.refresh_from_db()
        self.assertEqual(patient.current_station, self.discharge_station)

    def test_analytics_standard_metrics(self):
        patient = PatientWorkflow.objects.create(
            token_id='#A-106',
            patient_name='Analytics Patient',
            current_station=self.vitals_station
        )
        
        StationEntry.objects.create(
            patient=patient,
            station=self.vitals_station,
            data={
                'systolic_bp': 135,
                'diastolic_bp': 85,
                'glucose_level': 150,
                'weight_kg': 70,
                'height_cm': 175
            },
            client_submission_id='a1'
        )
        
        response = self.client.get('/api/patients/analytics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('blood_pressure_distribution', response.data)
        self.assertIn('bmi_distribution', response.data)
        self.assertIn('glucose_distribution', response.data)
        self.assertEqual(response.data['total_entries'], 1)
        self.assertEqual(response.data['blood_pressure_distribution']['Stage 1'], 1)
        self.assertEqual(response.data['bmi_distribution']['Normal'], 1)
        self.assertEqual(response.data['glucose_distribution']['Prediabetes'], 1)

    def test_analytics_dynamic_aggregation(self):
        patient = PatientWorkflow.objects.create(
            token_id='#A-107',
            patient_name='Dynamic Patient',
            current_station=self.vitals_station
        )
        
        StationEntry.objects.create(
            patient=patient,
            station=self.vitals_station,
            data={'systolic_bp': 120, 'diastolic_bp': 80, 'glucose_level': 100},
            client_submission_id='d1'
        )
        StationEntry.objects.create(
            patient=patient,
            station=self.vitals_station,
            data={'systolic_bp': 140, 'diastolic_bp': 90, 'glucose_level': 180},
            client_submission_id='d2'
        )
        
        response = self.client.get('/api/patients/analytics/', {'field': 'systolic_bp'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['field'], 'systolic_bp')
        self.assertEqual(response.data['aggregation']['120'], 1)
        self.assertEqual(response.data['aggregation']['140'], 1)
        self.assertEqual(response.data['total_entries'], 2)

    def test_analytics_filters_by_station_type(self):
        patient = PatientWorkflow.objects.create(
            token_id='#A-108',
            patient_name='Filter Patient',
            current_station=self.doctor_station
        )
        
        StationEntry.objects.create(
            patient=patient,
            station=self.doctor_station,
            data={'consultation_notes': 'Follow up required'},
            client_submission_id='f1'
        )
        
        response = self.client.get('/api/patients/analytics/', {'station_type': 'DOCTOR_TRIAGE'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_entries'], 1)
        self.assertEqual(response.data['station_type'], 'DOCTOR_TRIAGE')


class NFR1PerformanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='perfuser', password='perfpass')
        self.reg_role = RoleConfig.objects.create(role_name='Registration', schema=[])
        self.vitals_role = RoleConfig.objects.create(role_name='Vitals', schema=[])
        self.doctor_role = RoleConfig.objects.create(role_name='Doctor', schema=[])
        self.reg_station = ScreeningStation.objects.create(
            name='Reg', step_order=1, station_type='REGISTRATION',
            role_config=self.reg_role, is_active=True
        )
        self.vitals_station = ScreeningStation.objects.create(
            name='Vitals', step_order=2, station_type='VITALS',
            role_config=self.vitals_role, is_active=True
        )
        self.doctor_station = ScreeningStation.objects.create(
            name='Doctor', step_order=3, station_type='DOCTOR_TRIAGE',
            role_config=self.doctor_role, is_active=True
        )
        self.discharge_station = ScreeningStation.objects.create(
            name='Discharge', step_order=4, station_type='DISCHARGE',
            role_config=self.doctor_role, is_final_discharge=True, is_active=True
        )

    def test_token_generation_avoids_collisions(self):
        from screenings.models import PatientWorkflow
        tokens = set()
        for _ in range(50):
            token = PatientWorkflow.generate_token_id()
            self.assertNotIn(token, tokens)
            tokens.add(token)

    def test_discharge_completeness_uses_efficient_query(self):
        from screenings.services import DischargeService
        patient = PatientWorkflow.objects.create(
            token_id='#A-200',
            patient_name='Perf Test',
            current_station=self.discharge_station
        )
        StationEntry.objects.create(patient=patient, station=self.reg_station, data={}, client_submission_id='p1')
        StationEntry.objects.create(patient=patient, station=self.vitals_station, data={}, client_submission_id='p2')
        StationEntry.objects.create(patient=patient, station=self.doctor_station, data={}, client_submission_id='p3')
        StationEntry.objects.create(patient=patient, station=self.discharge_station, data={}, client_submission_id='p4')
        
        is_complete, missing = DischargeService.check_completeness(patient)
        self.assertTrue(is_complete)
        self.assertEqual(len(missing), 0)

    def test_active_stations_cached(self):
        from screenings.services import WorkflowService
        stations1 = WorkflowService.get_active_stations()
        self.assertEqual(len(stations1), 4)
        with self.assertNumQueries(0):
            stations2 = WorkflowService.get_active_stations()
            self.assertEqual(len(stations1), len(stations2))


class NFR2OfflineResiliencyTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        
        self.user = User.objects.create_user(username='offlineuser', password='offpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.reg_role = RoleConfig.objects.create(role_name='Registration', schema=[])
        self.vitals_role = RoleConfig.objects.create(role_name='Vitals', schema=[
            {'name': 'systolic_bp', 'type': 'number', 'required': True},
            {'name': 'diastolic_bp', 'type': 'number', 'required': True},
            {'name': 'glucose_level', 'type': 'number', 'required': True},
        ])
        self.reg_station = ScreeningStation.objects.create(
            name='Reg', step_order=1, station_type='REGISTRATION',
            role_config=self.reg_role, is_active=True
        )
        self.vitals_station = ScreeningStation.objects.create(
            name='Vitals', step_order=2, station_type='VITALS',
            role_config=self.vitals_role, is_active=True
        )

    def test_idempotent_submit_returns_existing_entry(self):
        patient = PatientWorkflow.objects.create(
            token_id='#B-101',
            patient_name='Offline Patient',
            current_station=self.vitals_station
        )
        submission_id = 'client-submission-123'

        payload = {
            'patient': patient.id,
            'station': self.vitals_station.id,
            'data': {
                'systolic_bp': 120,
                'diastolic_bp': 80,
                'glucose_level': 100
            },
            'client_submission_id': submission_id,
        }

        response1 = self.client.post('/api/entries/submit-and-advance/', payload, format='json')
        self.assertEqual(response1.status_code, 201)
        self.assertFalse(response1.data['duplicate'])

        response2 = self.client.post('/api/entries/submit-and-advance/', payload, format='json')
        self.assertEqual(response2.status_code, 200)
        self.assertTrue(response2.data['duplicate'])
        self.assertEqual(response2.data['entry']['client_submission_id'], submission_id)

    def test_batch_sync_creates_and_deduplicates(self):
        patient = PatientWorkflow.objects.create(
            token_id='#B-102',
            patient_name='Batch Patient',
            current_station=self.vitals_station
        )

        entries = [
            {
                'client_submission_id': 'batch-1',
                'patient': patient.id,
                'station': self.vitals_station.id,
                'data': {'systolic_bp': 120, 'diastolic_bp': 80, 'glucose_level': 100}
            },
            {
                'client_submission_id': 'batch-2',
                'patient': patient.id,
                'station': self.vitals_station.id,
                'data': {'systolic_bp': 140, 'diastolic_bp': 90, 'glucose_level': 180}
            }
        ]

        response = self.client.post('/api/entries/batch-sync/', {'entries': entries}, format='json')
        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['status'], 'created')
        self.assertEqual(results[1]['status'], 'created')

        # Duplicate sync
        response2 = self.client.post('/api/entries/batch-sync/', {'entries': entries}, format='json')
        self.assertEqual(response2.status_code, 200)
        results2 = response2.data['results']
        self.assertEqual(results2[0]['status'], 'duplicate')
        self.assertEqual(results2[1]['status'], 'duplicate')

    def test_batch_sync_handles_invalid_payload(self):
        entries = [
            {'patient': 999, 'station': 999, 'data': {}}
        ]
        response = self.client.post('/api/entries/batch-sync/', {'entries': entries}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['status'], 'error')


class NFR3DataIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='volunteer', password='volpass')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        self.client = APIClient()
        self.reg_role = RoleConfig.objects.create(role_name='Registration', schema=[])
        self.vitals_role = RoleConfig.objects.create(role_name='Vitals', schema=[])
        self.doctor_role = RoleConfig.objects.create(role_name='Doctor', schema=[])
        self.reg_station = ScreeningStation.objects.create(
            name='Reg', step_order=1, station_type='REGISTRATION',
            role_config=self.reg_role, is_active=True
        )
        self.vitals_station = ScreeningStation.objects.create(
            name='Vitals', step_order=2, station_type='VITALS',
            role_config=self.vitals_role, is_active=True
        )
        self.doctor_station = ScreeningStation.objects.create(
            name='Doctor', step_order=3, station_type='DOCTOR_TRIAGE',
            role_config=self.doctor_role, is_active=True
        )

    def test_locked_previous_station_entry_cannot_be_modified_by_non_admin(self):
        patient = PatientWorkflow.objects.create(
            token_id='#C-101',
            patient_name='Lock Test',
            current_station=self.doctor_station
        )
        entry = StationEntry.objects.create(
            patient=patient,
            station=self.reg_station,
            data={'full_name': 'Old Name'},
            client_submission_id='c1'
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f'/api/entries/{entry.id}/',
            {'data': {'full_name': 'New Name'}},
            format='json'
        )
        self.assertEqual(response.status_code, 403)

    def test_locked_previous_station_entry_can_be_modified_by_admin(self):
        patient = PatientWorkflow.objects.create(
            token_id='#C-102',
            patient_name='Admin Lock Test',
            current_station=self.doctor_station
        )
        entry = StationEntry.objects.create(
            patient=patient,
            station=self.reg_station,
            data={'full_name': 'Old Name'},
            client_submission_id='c2'
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f'/api/entries/{entry.id}/',
            {'data': {'full_name': 'New Name'}},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        entry.refresh_from_db()
        self.assertEqual(entry.data['full_name'], 'New Name')

    def test_current_station_entry_can_be_modified_by_non_admin(self):
        patient = PatientWorkflow.objects.create(
            token_id='#C-103',
            patient_name='Current Lock Test',
            current_station=self.vitals_station
        )
        entry = StationEntry.objects.create(
            patient=patient,
            station=self.vitals_station,
            data={'systolic_bp': 120},
            client_submission_id='c3'
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f'/api/entries/{entry.id}/',
            {'data': {'systolic_bp': 130}},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        entry.refresh_from_db()
        self.assertEqual(entry.data['systolic_bp'], 130)


class NFR4UsabilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='volunteer4', password='vol4pass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.reg_role = RoleConfig.objects.create(role_name='Registration', schema=[])
        self.vitals_role = RoleConfig.objects.create(role_name='Vitals', schema=[
            {'name': 'systolic_bp', 'type': 'number', 'required': True},
            {'name': 'diastolic_bp', 'type': 'number', 'required': True},
            {'name': 'glucose_level', 'type': 'number', 'required': True},
        ])
        self.reg_station = ScreeningStation.objects.create(
            name='Reg', step_order=1, station_type='REGISTRATION',
            role_config=self.reg_role, is_active=True
        )
        self.vitals_station = ScreeningStation.objects.create(
            name='Vitals', step_order=2, station_type='VITALS',
            role_config=self.vitals_role, is_active=True
        )
        self.doctor_station = ScreeningStation.objects.create(
            name='Doctor', step_order=3, station_type='DOCTOR_TRIAGE',
            role_config=self.vitals_role, is_active=True
        )

    def test_submit_response_includes_structured_alerts(self):
        patient = PatientWorkflow.objects.create(
            token_id='#D-101',
            patient_name='Alert Test',
            current_station=self.vitals_station
        )

        payload = {
            'patient': patient.id,
            'station': self.vitals_station.id,
            'data': {
                'systolic_bp': 190,
                'diastolic_bp': 80,
                'glucose_level': 100
            }
        }

        response = self.client.post('/api/entries/submit-and-advance/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['is_urgent'])
        self.assertEqual(len(response.data['alerts']), 1)
        self.assertEqual(response.data['alerts'][0]['type'], 'critical')
        self.assertEqual(response.data['alerts'][0]['field'], 'systolic_bp')

    def test_submit_response_alerts_empty_for_normal_vitals(self):
        patient = PatientWorkflow.objects.create(
            token_id='#D-102',
            patient_name='Normal Alert Test',
            current_station=self.vitals_station
        )

        payload = {
            'patient': patient.id,
            'station': self.vitals_station.id,
            'data': {
                'systolic_bp': 118,
                'diastolic_bp': 75,
                'glucose_level': 100
            }
        }

        response = self.client.post('/api/entries/submit-and-advance/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data['is_urgent'])
        self.assertEqual(len(response.data['alerts']), 0)

    def test_submit_response_includes_glucose_low_alert(self):
        patient = PatientWorkflow.objects.create(
            token_id='#D-103',
            patient_name='Glucose Low Test',
            current_station=self.vitals_station
        )

        payload = {
            'patient': patient.id,
            'station': self.vitals_station.id,
            'data': {
                'systolic_bp': 118,
                'diastolic_bp': 75,
                'glucose_level': 65
            }
        }

        response = self.client.post('/api/entries/submit-and-advance/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['is_urgent'])
        self.assertEqual(len(response.data['alerts']), 1)
        self.assertEqual(response.data['alerts'][0]['field'], 'glucose_level')
        self.assertIn('low', response.data['alerts'][0]['message'])






