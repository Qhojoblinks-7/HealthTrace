# HealthTrace - Community Health Screening Platform

A full-stack web application for community health screening, enabling volunteers to conduct health assessments and doctors to provide consultations and generate patient reports.

![HealthTrace](https://img.shields.io/badge/HealthTrace-Community%20Health%20Screening-blue)
![Django](https://img.shields.io/badge/Django-5.x-green)
![React](https://img.shields.io/badge/React-19-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Overview

HealthTrace is designed for community health outreach programs, particularly suitable for church communities, rural health initiatives, and mobile health clinics. The platform facilitates:

- **Volunteer-led Screening**: Community volunteers can capture patient vitals and basic health information
- **Real-time Health Analysis**: Automatic calculation of BMI, blood pressure status, and glucose categories
- **Doctor Consultation**: Medical professionals can review patients and provide recommendations
- **Report Generation**: Printable PDF reports with health assessments and doctor advice
- **Community Analytics**: Dashboard with health trends and disease prevalence data

## 🏗️ Architecture

```
HealthTrace/
├── healthtrace_be/          # Django REST API Backend
│   ├── core/                # Django project settings
│   ├── screenings/         # Main application (models, views, serializers)
│   ├── db.sqlite3          # SQLite database
│   └── requirements.txt    # Python dependencies
│
└── healthtrace-fe/          # React Frontend (Vite)
    ├── src/
    │   ├── components/      # React components
    │   │   ├── doctor/      # Doctor-facing components
    │   │   ├── volunteer/  # Volunteer screening components
    │   │   └── ui/          # Reusable UI components (shadcn)
    │   ├── pages/           # Page components
    │   ├── api.js           # API client configuration
    │   ├── store/           # Zustand state management
    │   └── App.jsx          # Main application component
    └── package.json         # Node.js dependencies
```

## ✨ Features

### Volunteer Features
- **Patient Intake Form**: Capture basic patient information (name, age, gender, contact)
- **Vitals Collection**: Enter blood pressure, glucose levels, heart rate, weight, and height
- **Live Results**: Real-time calculation of BMI and health status indicators
- **Screening Submission**: Save screenings to the database for doctor review

### Doctor Features
- **Patient Triage**: View today's patients with priority sorting (critical cases first)
- **Critical Alerts**: Immediate notification of hypertensive crisis and critical glucose levels
- **Consultation Interface**: Add doctor advice and mark patients for specialist follow-up
- **Notification System**: Track pending consultations and critical cases

### Analytics & Reporting
- **Community Dashboard**: View aggregate health statistics (age distribution, disease prevalence)
- **Printable Reports**: Generate professional PDF reports for patients
- **WhatsApp Sharing**: Send reports directly to patients via WhatsApp
- **Health Score**: Calculated overall health score based on vital signs

## 🛠️ Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Django | 5.x | Web framework |
| Django REST Framework | 3.14+ | REST API |
| SQLite | - | Database |
| Python-dotenv | - | Environment configuration |
| Django-cors-headers | 4.x | CORS handling |

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
| Recharts | 2.x | Charts and visualizations |
| Axios | 1.x | HTTP client |
| html2pdf.js | 0.14 | PDF generation |

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **npm** or **yarn**

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd healthtrace_be
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (edit `.env`):
   ```env
   DJANGO_SECRET_KEY=your-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   CORS_ALLOW_ALL_ORIGINS=True
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. (Optional) Populate sample data:
   ```bash
   python manage.py populate_data
   ```

7. Start the development server:
   ```bash
   python manage.py runserver
   ```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd healthtrace-fe
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment file (optional):
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

## 📱 Application Routes

| Route | Description |
|-------|-------------|
| `/` | Doctor Triage - Today's patient list |
| `/dashboard` | Community health analytics |
| `/consultation` | All consultations list |
| `/consultation/:id` | Clinical consultation page |
| `/reports` | Generate reports |
| `/report/:id` | Patient report (printable) |
| `/settings` | Application settings |

## 🔌 API Endpoints

### Screenings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/screenings/` | List all screenings (paginated) |
| POST | `/api/screenings/` | Create new screening |
| GET | `/api/screenings/{id}/` | Get screening details |
| PUT | `/api/screenings/{id}/` | Update screening |
| DELETE | `/api/screenings/{id}/` | Delete screening |
| POST | `/api/screenings/{id}/consult/` | Add doctor consultation |
| GET | `/api/screenings/summary/` | Get screening statistics |
| GET | `/api/screenings/notifications/` | Get critical alerts |
| GET | `/api/screenings/analytics/` | Community health data |

### Doctors

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/doctors/` | List all doctors |
| POST | `/api/doctors/` | Create doctor profile |
| GET | `/api/doctors/{id}/` | Get doctor details |

## 🏥 Health Calculations

### BMI (Body Mass Index)
```
BMI = weight (kg) / height (m)²
```
| Category | BMI Range |
|----------|------------|
| Underweight | < 18.5 |
| Normal | 18.5 - 24.9 |
| Overweight | 25 - 29.9 |
| Obese | ≥ 30 |

### Blood Pressure (American Heart Association)
| Category | Systolic | Diastolic |
|----------|----------|-----------|
| Normal | < 120 | < 80 |
| Elevated | 120-129 | < 80 |
| Stage 1 | 130-139 | OR 80-89 |
| Stage 2 | ≥ 140 | OR ≥ 90 |
| Crisis | > 180 | OR > 120 |

### Blood Glucose (American Diabetes Association)
| Category | Glucose (mg/dL) |
|----------|----------------|
| Normal | < 140 |
| Prediabetes | 140-199 |
| Diabetes | ≥ 200 |

## 📦 Deployment

### Production Build

**Backend:**
```bash
cd healthtrace_be
python manage.py collectstatic
python manage.py migrate
```

**Frontend:**
```bash
cd healthtrace-fe
npm run build
```

The build output will be in the `dist/` folder.

### Environment Variables

For production, update the `.env` file:

```env
DJANGO_SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

## 📄 Models

### Screening Model
The main model capturing patient health data:

- **Personal Info**: full_name, age, gender, phone_number, email
- **Measurements**: weight_kg, height_cm, bmi (calculated)
- **Vitals**: systolic_bp, diastolic_bp, glucose_level, heart_rate
- **Medical History**: known_conditions, current_medications
- **Consultation**: doctor, doctor_advice, requires_specialist_followup, consultation_date
- **Metadata**: screened_by, created_at, updated_at

### Doctor Model
Linked to Django's User model:

- **User**: One-to-one link with Django auth
- **phone_number**: Contact number
- **specialization**: Medical specialization
- **license_number**: Medical license

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [shadcn/ui](https://ui.shadcn.com/) for the beautiful component library
- [Django](https://www.djangoproject.com/) for the robust backend framework
- [React](https://react.dev/) for the modern frontend framework
- Community health workers worldwide for their dedication

---

Built with ❤️ for community health
#   H e a l t h T r a c e 
 
 
