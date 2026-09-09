An operational software requirements specification for HealthTrace, structured using Design Science Research Methodology (DSRM) to establish research and design rigor, alongside an Agile Software Development Life Cycle (SDLC) for execution and implementation.
1. Design Science Research Methodology (DSRM) Framework
DSRM ensures the platform addresses operational field problems with a validated architectural artifact.



┌───────────────────────────────────────────────────────────────────────────────────┐
│                                DSRM PROCESS CYCLE                                 │
└───────────────────────────────────────────────────────────────────────────────────┘
 ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │  1. Problem  │──►│ 2. Objectives│──►│ 3. Design &  │──►│4. Demonstra- │──►│5. Evaluation │
 │  Definition  │   │  of Solution │   │ Development  │   │     tion     │   │ & Communication
 └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘


Phase 1: Problem Identification & Motivation
Problem Statement: Live community health screenings face data corruption, row overwrites, and mismatched schema columns due to concurrent manual entry on shared spreadsheets.
Operational Bottlenecks:
Multi-station friction (Registration $\rightarrow$ Vitals $\rightarrow$ Doctor/Lab $\rightarrow$ Admin Discharge).
Inconsistent risk triage and delayed identification of clinical emergencies.
Field connectivity drops leading to data loss.
Inability to modify schema inputs mid-event without breaking legacy records.
Phase 2: Objectives of a Solution
Architectural Objectives:
Build a role-based, dynamic schema platform operating on isolated device queues.
Automate risk category calculation (AHA Blood Pressure stages, ADA Glucose classifications, BMI).
Implement conditional, station-by-station patient queue routing.
Enforce final administrative review, record locking, and discharge dispatching.
Phase 3: Design & Development (The Artifact)
Core Artifact: Full-stack web application (Django REST API backend + React 19 Vite frontend).
Sub-Artifacts:
Schema-driven JSON form engine (RoleConfig).
Real-time station queue routing engine (PatientWorkflow).
Dynamic analytics visualization system using Recharts.
Phase 4: Demonstration
Deployment of local dev instance (http://localhost:8000 & http://localhost:5173) simulating a 4-table field drive (Registration $\rightarrow$ Vitals $\rightarrow$ Lab/Doctor $\rightarrow$ Admin Discharge) using synthetic patient workloads.
Phase 5: Evaluation
Performance metrics evaluated against field benchmarks: zero row overwrites, sub-second station transfers, sub-200ms API response latency, and successful offline storage recovery via IndexedDB.
Phase 6: Communication
Artifact technical specifications documented via OpenAPI/Swagger endpoints, system architecture diagrams, and open-source documentation.
2. SDLC Implementation Framework (Agile-Scrum)
SDLC Phases & Milestones
SDLC Phase
Focus & Deliverables
Primary Stack Components
Phase 1: Inception & Architecture
Data models (RoleConfig, PatientWorkflow), API contracts, dynamic JSON schemas
Django 5.x, PostgreSQL/SQLite, DRF
Phase 2: Core Engineering
Role-based authentication, dynamic form renderer, automated vitals logic engine
React 19, Tailwind CSS v4, Zustand 5, TanStack Query 5
Phase 3: Station Routing
Queue management API, triage alerts, station lock mechanisms
React Router 7, Django REST Framework, Axios
Phase 4: Discharge & Reporting
PDF summary generation, WhatsApp dispatching, Recharts analytical dashboard
html2pdf.js, Recharts 2.x, Twilio/WhatsApp API
Phase 5: Field Hardening
IndexedDB offline sync, user acceptance testing (UAT), production builds
Vite build tools, Service Workers

3. System Functional Requirements



                       ┌─────────────────────────────────────────┐
                       │        TABLE 1: REGISTRATION            │
                       │ Registers Patient ➔ Generates Token ID  │
                       └────────────────────┬────────────────────┘
                                            │
                                            ▼
                       ┌─────────────────────────────────────────┐
                       │            TABLE 2: VITALS              │
                       │ Captures BP, Glucose ➔ Dynamic Schema    │
                       └────────────────────┬────────────────────┘
                                            │
                             ┌──────────────┴──────────────┐
                             │  Conditional Route Check    │
                             └──────────────┬──────────────┘
                                            │
                 ┌──────────────────────────┴──────────────────────────┐
                 ▼                                                     ▼
┌─────────────────────────────────┐                   ┌─────────────────────────────────┐
│     CRITICAL / ELEVATED RISK    │                   │           NORMAL RANGE          │
│ TABLE 3A: LAB / DOCTOR TRIAGE   │                   │   TABLE 3B: GENERAL CHECKOUT    │
│ Emergency Flags & Consult Notes │                   │   General Medical Observations  │
└────────────────┬────────────────┘                   └────────────────┬────────────────┘
                 │                                                     │
                 └──────────────────────────┬──────────────────────────┘
                                            │
                                            ▼
                       ┌─────────────────────────────────────────┐
                       │        TABLE 4: ADMIN DISCHARGE         │
                       │ Completeness Check ➔ Lock ➔ PDF/WhatsApp│
                       └─────────────────────────────────────────┘


FR-1: Dynamic Role & Schema Management
FR-1.1: System shall allow Administrators to define custom roles (RoleConfig) linked to specific screening stages.
FR-1.2: System shall allow Admins to edit a JSONField schema defining input type (number, text, checkbox, dropdown), requirement state, and visual labels per role.
FR-1.3: Form Renderer shall dynamically generate form controls based on fetched active role schemas without requiring frontend redeployment.
FR-2: Automated Health Calculations & Triage Logic
FR-2.1: System shall compute BMI immediately upon input of height ($m$) and weight ($kg$):
$$\text{BMI} = \frac{\text{weight (kg)}}{\text{height (m)}^2}$$
FR-2.2: System shall categorize blood pressure using AHA guidelines (Normal, Elevated, Stage 1, Stage 2, Hypertensive Crisis).
FR-2.3: System shall categorize blood glucose levels based on ADA standards (Normal $<140\text{ mg/dL}$, Prediabetes $140\text{--}199\text{ mg/dL}$, Diabetes $\ge 200\text{ mg/dL}$).
FR-2.4: System shall evaluate incoming vitals and automatically assign emergency triage status (is_urgent = True) if Systolic $\ge 180$, Diastolic $\ge 120$, or Glucose $\ge 250\text{ mg/dL}$.
FR-3: Sequential Multi-Station Workflow & Queue Routing
FR-3.1: Table 1 (Registration): Generates a unique Patient ID / Token Number (e.g., #A-104) and initializes the state machine to REGISTRATION.
FR-3.2: Table 2 (Vitals): Submits vital parameters and executes automated backend routing logic to assign the next station (DOCTOR_TRIAGE, LAB_GLUCOSE, or DISCHARGE).
FR-3.3: Table 3 (Doctor / Lab): Displays filtered station queue. Doctors record specialist consultation notes and diagnostic follow-ups.
FR-3.4: Table 4 (Admin / Discharge):
Verifies data completeness across all prior stations.
Allows administrative override to fix miskeyed numbers (e.g., BP entered as 1800).
Locks record (is_discharged = True) preventing post-exit edits.
Dispatches printable PDF report (html2pdf.js) and triggers WhatsApp message delivery.
FR-4: Analytics & Dynamic Data Visualization
FR-4.1: System shall aggregate key standard metrics (BP ranges, BMI distributions, Glucose categories) in real-time.
FR-4.2: System shall provide query endpoints to aggregate key-value pairs stored inside custom_data JSON to generate dynamic bar charts via Recharts.
4. Non-Functional Requirements (NFR)
NFR-1: Performance & Latency:
API response time for screening submission must remain $< 200\text{ ms}$ under normal station load.
Queue auto-refresh intervals must cycle within $3\text{ seconds}$ without dropping active input focus.
NFR-2: Reliability & Offline Resiliency:
System shall utilize IndexedDB / localStorage caching to capture station submissions during local Wi-Fi drops.
Cached submissions shall automatically sync to Django API upon network restoration without duplicate row creation.
NFR-3: Data Integrity & Security:
Form submissions must validate against backend serializers before storage.
Station inputs lock upon transition; previous station records cannot be modified without Admin credentials.
NFR-4: Usability & Accessibility:
Interfaces must be responsive across mobile devices, tablets, and desktop setups.
Field forms must feature high-contrast input controls and bold alert banners for critical vitals.
5. Technical Requirements & API Contracts
Data Schemas (Django REST API)



Python
# screenings/models.py
from django.db import models
from django.contrib.auth.models import User

class RoleConfig(models.Model):
    role_name = models.CharField(max_length=50, unique=True)
    schema = models.JSONField(default=list)  # Form schema definition

class PatientWorkflow(models.Model):
    STATION_CHOICES = [
        ('REGISTRATION', 'Table 1: Registration'),
        ('VITALS', 'Table 2: Basic Vitals'),
        ('LAB_GLUCOSE', 'Table 3A: Glucose / Lab'),
        ('DOCTOR_TRIAGE', 'Table 3B: Doctor Consultation'),
        ('DISCHARGE', 'Table 4: Admin Discharge'),
        ('COMPLETED', 'Completed'),
    ]

    token_id = models.CharField(max_length=20, unique=True)
    patient_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True)
    current_station = models.CharField(max_length=30, choices=STATION_CHOICES, default='REGISTRATION')
    is_urgent = models.BooleanField(default=False)
    is_discharged = models.BooleanField(default=False)
    
    # Station Payload Buckets
    vitals_data = models.JSONField(default=dict)
    lab_data = models.JSONField(default=dict)
    custom_data = models.JSONField(default=dict)
    doctor_notes = models.TextField(blank=True)
    
    discharged_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


Core API Endpoints
Method
Endpoint
Description
GET
/api/roles/
List all role configurations and active dynamic schemas
POST
/api/roles/
Create/modify a role configuration schema
GET
/api/screenings/queue/?station={STATION_NAME}
Fetch real-time patient queue filtered by active table
POST
/api/screenings/
Register new patient (Table 1) and issue Token ID
PUT
/api/screenings/{id}/vitals/
Submit vitals (Table 2) and execute auto-routing logic
POST
/api/screenings/{id}/discharge/
Admin discharge checkout (Table 4), lock record, trigger PDF/WhatsApp
GET
/api/screenings/analytics/dynamic/
Aggregated JSON metric counts for Recharts rendering


