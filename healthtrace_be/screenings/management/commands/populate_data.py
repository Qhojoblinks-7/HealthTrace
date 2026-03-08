from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from screenings.models import Doctor, Screening
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Populate database with dummy screening data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of screening records to create',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write('Creating dummy data...')
        
        # Create a test doctor
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
        
        doctor, created = Doctor.objects.get_or_create(
            user=user,
            defaults={
                'phone_number': '+233501234567',
                'specialization': 'General Practitioner',
                'license_number': 'MD-12345-GH',
            }
        )
        
        # Sample data for generating realistic values
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
        
        conditions = [
            'None', 'Hypertension', 'Diabetes Type 2', 'Asthma', 
            'Arthritis', 'None', 'None', 'None'
        ]
        
        medications = [
            'None', 'Metformin', 'Amlodipine', 'Aspirin', 
            'None', 'None', 'Lisinopril', 'Glibenclamide'
        ]
        
        volunteers = ['Sarah J.', 'Michael K.', 'Grace A.', 'Paul O.', 'Mary W.']
        
        # Create screenings
        created_count = 0
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            full_name = f"{first_name} {last_name}"
            
            # Age distribution: more middle-aged and elderly
            age_weights = [5, 15, 25, 25, 15, 10, 5]  # 0-17, 18-30, 31-45, 46-60, 60+
            age = random.choices(
                [random.randint(5, 17), random.randint(18, 30), random.randint(31, 45), 
                 random.randint(46, 60), random.randint(61, 75), random.randint(76, 85), 
                 random.randint(86, 95)],
                weights=age_weights
            )[0]
            
            gender = random.choice(['Male', 'Female'])
            
            # Generate realistic vitals
            # BMI: mostly overweight/obese in this population
            bmi = random.choices(
                [random.uniform(18, 24), random.uniform(25, 29), random.uniform(30, 35), random.uniform(36, 45)],
                weights=[30, 35, 25, 10]
            )[0]
            height = random.uniform(155, 185)  # cm
            weight = bmi * (height/100) ** 2  # kg
            
            # Blood pressure: many with elevated/high BP
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
            else:  # crisis
                systolic = random.randint(180, 210)
                diastolic = random.randint(120, 140)
            
            # Glucose: some with elevated levels
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
            
            # Random date within last 30 days
            days_ago = random.randint(0, 30)
            created_date = timezone.now() - timedelta(days=days_ago)
            
            # 30% chance of having consultation
            has_consultation = random.random() < 0.3
            
            screening = Screening(
                full_name=full_name,
                age=age,
                gender=gender,
                phone_number=f'+233{random.randint(200000000, 999999999)}',
                email=f'{first_name.lower()}.{last_name.lower()}@email.com',
                weight_kg=round(weight, 2),
                height_cm=round(height, 2),
                systolic_bp=systolic,
                diastolic_bp=diastolic,
                glucose_level=round(glucose, 2),
                heart_rate=heart_rate,
                known_conditions=random.choice(conditions),
                current_medications=random.choice(medications),
                notes=f'Routine health screening. Patient reports {random.choice(["no symptoms", "occasional headaches", "fatigue", "good health"])}.',
                screened_by=random.choice(volunteers),
                created_at=created_date,
            )
            
            if has_consultation:
                screening.doctor = doctor
                screening.doctor_advice = random.choice([
                    'Continue current medication. Monitor BP daily.',
                    'Reduce salt intake, exercise regularly. Follow up in 3 months.',
                    'Referred to specialist for further evaluation.',
                    'Lifestyle modifications recommended. Low-sodium diet.',
                    'Maintain healthy weight. Regular checkups recommended.',
                    'Medication review needed. Schedule appointment.',
                ])
                screening.consultation_date = created_date + timedelta(hours=random.randint(1, 48))
            
            screening.save()
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {created_count} screening records'
        ))
        
        # Print summary
        total = Screening.objects.count()
        high_bp = Screening.objects.filter(
            systolic_bp__gte=140
        ).count()
        with_consultation = Screening.objects.filter(doctor__isnull=False).count()
        
        self.stdout.write(f'Total screenings: {total}')
        self.stdout.write(f'High BP cases: {high_bp} ({round(high_bp/total*100, 1)}%)')
        self.stdout.write(f'With consultation: {with_consultation} ({round(with_consultation/total*100, 1)}%)')
