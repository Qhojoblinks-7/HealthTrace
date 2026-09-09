
# HealthTrace & Engineering Workflow Rules

## 1. Developer Profile & Preferred Tech Stack

### Web & Mobile Stack
- **Frontend Framework:** React 19 (Vite 7) with pure JavaScript (`.js` / `.jsx`). **NO TypeScript.** Use `prop-types` for component property validation when necessary.
- **UI & Styling:** Tailwind CSS v4, `shadcn/ui` component primitives, and Lucide React icons.
- **State & Data Fetching:** TanStack Query v5 (React Query) for server state/caching, Zustand v5 for global client state, and Axios v1.x for API requests.
- **Routing & Visuals:** React Router v7 and Recharts v2.x for analytics.
- **Backend Framework:** Django 5.x with Django REST Framework (DRF) 3.14+, Python 3.10+, and SQLite (local dev) / PostgreSQL (production target).
- **Mobile Target (when applicable):** React Native (Expo) with TanStack Query and Zustand.

---

## 2. Code Quality & Workflow Rules

### Commenting & Documentation
- **Intent-Driven Comments:** Do NOT comment self-explanatory lines (e.g., `// set loading to true`). Write clear comments explaining **WHY** complex clinical calculations, dynamic schema mappings, or workflow state transitions exist.
- **Docstrings & JSDoc:** 
  - Every Django API view function/class and utility function MUST have concise docstrings describing parameters, calculated outputs, and side effects.
  - Every React helper utility or custom hook MUST include JSDoc comments explaining input schemas and return payloads.
- **Refactoring & TODOS:** Explicitly tag temporary workarounds or field fallback logic with `// TODO (Field-Drive): <reason>`.

### Error Handling & Resiliency
- **Explicit Try/Catch Boundaries:** Never leave asynchronous API calls (`async/await`) unhandled. Always wrap them in `try/catch` blocks or leverage TanStack Query's `onError` / `catch` handlers.
- **Graceful UI Fallbacks:** 
  - Show intuitive, non-blocking toast notifications or alert banners for API errors rather than breaking the application interface.
  - Include zero-state UI cards when station queues or analytics datasets are empty.
- **Backend Payload Validation:** 
  - Validate all dynamic JSON payloads (`custom_data`) against serializer rules before persisting to the database.
  - Return clear, structured JSON error messages (`{"error": "Description", "field": "field_name"}`) with appropriate HTTP status codes (`400`, `404`, `500`).

---

## 3. Architecture & Domain Rules (HealthTrace Field Drive)

### Multi-Station Queue Workflow
1. **Table 1 (Registration):** Generates a unique Token ID (e.g., `#A-104`) and initializes `current_station = 'REGISTRATION'`.
2. **Table 2 (Vitals):** Captures BP, Glucose, BMI, and executes backend logic to evaluate AHA/ADA risk categories. Conditionally updates `current_station` based on risk severity.
3. **Table 3 (Doctor / Lab):** Receives routed patients for clinical notes or specialized tests.
4. **Table 4 (Admin / Discharge - Final Gatekeeper):** Reviews multi-station data completeness, allows administrative overrides to fix miskeys, locks the record (`is_discharged = True`), and dispatches printable PDF summaries (`html2pdf.js`) / WhatsApp reports.

### Database & Schema Rules
- **Schema-Driven Forms:** Render intake controls dynamically using schema configs (`RoleConfig.schema`). Never hardcode fields that vary by screening role.
- **Data Bucket Isolation:** Store station-specific inputs in dedicated JSON buckets (`vitals_data`, `lab_data`, `custom_data`) to prevent cross-table overwrites.

---

## 4. Standard Code Snippets & Blueprints

### A. React Async Handler & Error Catching Standard
```jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import axios from 'axios';

/**
 * Handles station form submissions with explicit error bounds and user feedback.
 */
export function StationSubmitButton({ patientId, stationData, onSuccess }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await axios.post(`/api/screenings/${patientId}/vitals/`, stationData);
      if (response.data?.status === 'Success') {
        onSuccess(response.data);
      }
    } catch (err) {
      // Extract backend validation detail or default to generic message
      const detail = err.response?.data?.error || 'Failed to submit station vitals. Please check connection.';
      setErrorMessage(detail);
      console.error('[StationSubmit Error]:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-2">
      {errorMessage && (
        <div className="p-3 text-xs bg-red-50 border border-red-200 text-red-700 rounded-lg">
          {errorMessage}
        </div>
      )}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={isSubmitting}
        className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50"
      >
        {isSubmitting ? 'Routing Patient...' : 'Submit & Route to Next Station'}
      </button>
    </div>
  );
}

StationSubmitButton.propTypes = {
  patientId: PropTypes.number.isRequired,
  stationData: PropTypes.object.isRequired,
  onSuccess: PropTypes.func.isRequired,
};

```

### B. Django DRF Error-Safe View Standard

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)

class SubmitVitalsView(APIView):
    """
    Receives Table 2 vitals data, evaluates clinical thresholds,
    and calculates the next station queue assignment.
    """
    def post(self, request, patient_id):
        try:
            # 1. Fetch patient workflow record
            patient = PatientWorkflow.objects.get(id=patient_id)
            vitals = request.data.get('vitals_data', {})

            if not vitals:
                return Response(
                    {"error": "Vitals payload cannot be empty."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. Extract key vitals with fallback safety
            systolic = int(vitals.get('systolic', 0))
            glucose = float(vitals.get('glucose', 0))

            patient.vitals_data = vitals

            # 3. Clinical Triage Logic (AHA / ADA Guidelines)
            if systolic >= 180 or glucose >= 250:
                patient.current_station = 'DOCTOR_TRIAGE'
                patient.is_urgent = True
            elif glucose >= 140:
                patient.current_station = 'LAB_GLUCOSE'
            else:
                patient.current_station = 'DOCTOR_TRIAGE'

            patient.save()

            return Response({
                "status": "Success",
                "next_station": patient.current_station,
                "is_urgent": patient.is_urgent
            }, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response(
                {"error": f"Patient ID {patient_id} not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except (ValueError, TypeError) as e:
            logger.error(f"Malformed vitals input for patient {patient_id}: {str(e)}")
            return Response(
                {"error": "Invalid numerical values provided for BP or Glucose."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.critical(f"Unexpected system error in SubmitVitalsView: {str(e)}")
            return Response(
                {"error": "An internal server error occurred while processing vitals."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

```

```

<ElicitationsGroup message="Where would you like to place or expand this rules file?">
  <Elicitation label="Save as .kilocode/rules for Kilo Code AI assistant" query="How do I place this configuration into the .kilocode/rules folder for VS Code and Kilo Code integration?"/>
  <Elicitation label="Add offline IndexedDB error recovery rules" query="Add specific error handling and local storage fallback rules for offline Wi-Fi drops to the configuration."/>
</ElicitationsGroup>

```