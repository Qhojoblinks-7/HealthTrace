from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from screenings.models import (
    RoleConfig,
    ScreeningStation,
    PatientWorkflow,
    StationEntry,
)


class Command(BaseCommand):
    help = 'Populate database with dummy screening data using new models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of patient records to create',
        )

    def handle(self, *args, **options):
        count = options['count']

        self.stdout.write('Creating dummy data...')

        user, created = User.objects.get_or_create(
            username='dr_test',
            defaults={
                'first_name': 'John',
                'last_name': 'Smith',
                'email': 'dr.smith@healthtrace.org',
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()

        registration_station = ScreeningStation.objects.filter(step_order=1).first()
        vitals_station = ScreeningStation.objects.filter(step_order=2).first()
        discharge_station = ScreeningStation.objects.filter(is_final_discharge=True).first()

        if not all([registration_station, vitals_station, discharge_station]):
            self.stdout.write(self.style.ERROR(
                'Required stations not found. Run setup_stations first.'
            ))
            return

        first_names = [
            'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer',
            'Michael', 'Linda', 'William', 'Elizabeth', 'David', 'Barbara',
            'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah',
            'Charles', 'Karen', 'Kwame', 'Abena', 'Kofi', 'Akua', 'Yaw', 'Adjoa'
        ]

        last_names = [
            'Williams', 'Johnson', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Anderson', 'Taylor', 'Thomas',
            'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White',
            'Asante', 'Osei', 'Mensah', 'Kwaku', 'Yaw', 'Adom', 'Baba'
        ]

        volunteers = ['Sarah J.', 'Michael K.', 'Grace A.', 'Paul O.', 'Mary W.']

        created_count = 0
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            full_name = f"{first_name} {last_name}"

            age_weights = [5, 15, 25, 25, 15, 10, 5]
            age = random.choices(
                [random.randint(5, 17), random.randint(18, 30), random.randint(31, 45),
                 random.randint(46, 60), random.randint(61, 75), random.randint(76, 85),
                 random.randint(86, 95)],
                weights=age_weights
            )[0]

            gender = random.choice(['Male', 'Female'])

            bmi = random.choices(
                [random.uniform(18, 24), random.uniform(25, 29), random.uniform(30, 35), random.uniform(36, 45)],
                weights=[30, 35, 25, 10]
            )[0]
            height = random.uniform(155, 185)
            weight = bmi * (height/100) ** 2

            bp_choice = random.choices(
                ['normal', 'elevated', 'stage1', 'stage2', 'crisis'],
                weights=[40, 20, 20, 15, 5]
            )[0]

            if bp_choice == 'normal':
                systolic = random.randint(90, 119)
                diastolic = random.randint(60, 79)
            elif bp_choice == 'elevated':
                systolic = random.randint(120, 129)
                diastolic = random.randint(60, 79)
            elif bp_choice == 'stage1':
                systolic = random.randint(130, 139)
                diastolic = random.randint(80, 89)
            elif bp_choice == 'stage2':
                systolic = random.randint(140, 179)
                diastolic = random.randint(90, 119)
            else:
                systolic = random.randint(180, 210)
                diastolic = random.randint(120, 140)

            glucose_choice = random.choices(
                ['normal', 'prediabetes', 'diabetes'],
                weights=[60, 25, 15]
            )[0]

            if glucose_choice == 'normal':
                glucose = random.uniform(70, 130)
            elif glucose_choice == 'prediabetes':
                glucose = random.uniform(140, 190)
            else:
                glucose = random.uniform(200, 350)

            heart_rate = random.randint(55, 100)

            days_ago = random.randint(0, 30)
            created_date = timezone.now() - timedelta(days=days_ago)

            token_id = f"#{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}-{random.randint(100, 999)}"

            patient = PatientWorkflow(
                token_id=token_id,
                patient_name=full_name,
                phone_number=f'+233{random.randint(200000000, 999999999)}',
                created_at=created_date,
            )

            is_urgent = systolic >= 180 or diastolic >= 120 or glucose >= 200 or glucose <= 70
            patient.is_urgent = is_urgent

            has_consultation = random.random() < 0.3
            if has_consultation:
                patient.is_completed = True
                patient.current_station = None
            else:
                patient.current_station = discharge_station

            patient.save()

            StationEntry.objects.create(
                patient=patient,
                station=registration_station,
                recorded_by=user,
                data={
                    'full_name': full_name,
                    'age': age,
                    'gender': gender,
                    'phone_number': patient.phone_number,
                },
                notes='Routine health screening.',
                created_at=created_date,
            )

            StationEntry.objects.create(
                patient=patient,
                station=vitals_station,
                recorded_by=user,
                data={
                    'systolic_bp': systolic,
                    'diastolic_bp': diastolic,
                    'glucose_level': round(glucose, 2),
                    'heart_rate': heart_rate,
                    'weight_kg': round(weight, 2),
                    'height_cm': round(height, 2),
                },
                notes=f"Screened by {random.choice(volunteers)}.",
                created_at=created_date + timedelta(minutes=5),
            )

            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {created_count} patient records'
        ))

        total = PatientWorkflow.objects.count()
        urgent_count = PatientWorkflow.objects.filter(is_urgent=True).count()
        completed = PatientWorkflow.objects.filter(is_completed=True).count()

        self.stdout.write(f'Total patients: {total}')
        if total > 0:
            self.stdout.write(f'Urgent cases: {urgent_count} ({round(urgent_count/total*100, 1)}%)')
            self.stdout.write(f'Completed: {completed} ({round(completed/total*100, 1)}%)')