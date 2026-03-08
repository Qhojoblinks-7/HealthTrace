
---

# 🏥 HealthTrace – Community Health Screening Platform

A **full-stack web application** for community health screening, enabling volunteers to conduct health assessments and doctors to provide consultations and generate patient reports.

`https://img.shields.io/badge/HealthTrace-Community%20Health%20Screening-blue`
`https://img.shields.io/badge/Django-5.x-green`
`https://img.shields.io/badge/React-19-blue`
`https://img.shields.io/badge/License-MIT-yellow`

---

## 📋 Overview

**HealthTrace** is designed for community health outreach programs—ideal for church communities, rural health initiatives, and mobile health clinics.  

It provides:

- **Volunteer-led Screening**: Capture patient vitals and basic health information  
- **Real-time Health Analysis**: Automatic calculation of BMI, blood pressure status, and glucose categories  
- **Doctor Consultation**: Medical professionals can review patients and provide recommendations  
- **Report Generation**: Printable PDF reports with health assessments and doctor advice  
- **Community Analytics**: Dashboard with health trends and disease prevalence data  

---

## 🏗️ Architecture

```
HealthTrace/
├── healthtrace_be/          # Django REST API Backend
│   ├── core/                # Django project settings
│   ├── screenings/          # Models, views, serializers
│   ├── db.sqlite3           # SQLite database
│   └── requirements.txt     # Python dependencies
│
└── healthtrace-fe/          # React Frontend (Vite)
    ├── src/
    │   ├── components/      # React components
    │   │   ├── doctor/      # Doctor-facing components
    │   │   ├── volunteer/   # Volunteer screening components
    │   │   └── ui/          # Reusable UI (shadcn)
    │   ├── pages/           # Page components
    │   ├── api.js           # API client config
    │   ├── store/           # Zustand state management
    │   └── App.jsx          # Main app entry
    └── package.json         # Node.js dependencies
```

---

## ✨ Features

### 👩‍⚕️ Volunteer
- Patient intake form (basic info)  
- Vitals collection (BP, glucose, heart rate, weight, height)  
- Live BMI & health status calculation  
- Screening submission for doctor review  

### 🩺 Doctor
- Patient triage (critical cases first)  
- Critical alerts (hypertensive crisis, glucose emergencies)  
- Consultation interface (advice, specialist follow-up)  
- Notification system for pending consultations  

### 📊 Analytics & Reporting
- Community dashboard (aggregate statistics)  
- Printable PDF reports  
- WhatsApp report sharing  
- Overall health score calculation  

---

## 🛠️ Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Django | 5.x | Web framework |
| Django REST Framework | 3.14+ | REST API |
| SQLite | - | Database |
| python-dotenv | - | Env configuration |
| django-cors-headers | 4.x | CORS handling |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.x | UI framework |
| Vite | 7.x | Build tool |
| Tailwind CSS | 4.x | Styling |
| shadcn/ui | 4.x | Component library |
| React Router | 7.x | Navigation |
| React Query | 5.x | Data fetching |
| Zustand | 5.x | State management |
| Recharts | 2.x | Charts |
| Axios | 1.x | HTTP client |
| html2pdf.js | 0.14 | PDF generation |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+  
- Node.js 18+  
- npm or yarn  

### Backend Setup
```bash
cd healthtrace_be
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
Backend runs at: **http://localhost:8000**

### Frontend Setup
```bash
cd healthtrace-fe
npm install
npm run dev
```
Frontend runs at: **http://localhost:5173**

---

## 📱 Application Routes

| Route | Description |
|-------|-------------|
| `/` | Doctor triage – today’s patients |
| `/dashboard` | Community health analytics |
| `/consultation` | All consultations list |
| `/consultation/:id` | Clinical consultation page |
| `/reports` | Generate reports |
| `/report/:id` | Printable patient report |
| `/settings` | Application settings |

---

## 🔌 API Endpoints

### Screenings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/screenings/` | List screenings |
| POST | `/api/screenings/` | Create screening |
| GET | `/api/screenings/{id}/` | Screening details |
| PUT | `/api/screenings/{id}/` | Update screening |
| DELETE | `/api/screenings/{id}/` | Delete screening |
| POST | `/api/screenings/{id}/consult/` | Add consultation |
| GET | `/api/screenings/summary/` | Screening stats |
| GET | `/api/screenings/notifications/` | Critical alerts |
| GET | `/api/screenings/analytics/` | Community health data |

### Doctors
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/doctors/` | List doctors |
| POST | `/api/doctors/` | Create doctor profile |
| GET | `/api/doctors/{id}/` | Doctor details |

---

## 🏥 Health Calculations

### BMI
\[
BMI = \frac{weight (kg)}{height (m)^2}
\]

| Category | BMI Range |
|----------|------------|
| Underweight | < 18.5 |
| Normal | 18.5–24.9 |
| Overweight | 25–29.9 |
| Obese | ≥ 30 |

### Blood Pressure (AHA)
| Category | Systolic | Diastolic |
|----------|----------|-----------|
| Normal | < 120 | < 80 |
| Elevated | 120–129 | < 80 |
| Stage 1 | 130–139 | OR 80–89 |
| Stage 2 | ≥ 140 | OR ≥ 90 |
| Crisis | > 180 | OR > 120 |

### Blood Glucose (ADA)
| Category | Glucose (mg/dL) |
|----------|----------------|
| Normal | < 140 |
| Prediabetes | 140–199 |
| Diabetes | ≥ 200 |

---

## 📦 Deployment

### Backend
```bash
cd healthtrace_be
python manage.py collectstatic
python manage.py migrate
```

### Frontend
```bash
cd healthtrace-fe
npm run build
```
Build output: `dist/`

---

## 📄 Models

### Screening
- Personal info (name, age, gender, contact)  
- Measurements (weight, height, BMI)  
- Vitals (BP, glucose, heart rate)  
- Medical history (conditions, medications)  
- Consultation (doctor, advice, follow-up, date)  
- Metadata (screened_by, created_at, updated_at)  

### Doctor
- Linked to Django User  
- Phone number  
- Specialization  
- License number  

---

## 🤝 Contributing
1. Fork the repo  
2. Create a feature branch  
3. Commit changes  
4. Push branch  
5. Open a Pull Request  

---

## 📝 License
MIT License – see LICENSE file.

---

## 🙏 Acknowledgments
- [shadcn/ui](https://ui.shadcn.com/)  
- [Django](https://www.djangoproject.com/)  
- [React](https://react.dev/)  
- Community health workers worldwide  

---

✨ Built with ❤️ for community health ✨  

---
