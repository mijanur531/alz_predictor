# 🧠 AlzPredictor — Enterprise Neurological Health & Alzheimer's Prediction Platform

[![CI/CD Pipeline](https://github.com/mijanur531/alz_predictor/actions/workflows/django.yml/badge.svg)](https://github.com/mijanur531/alz_predictor/actions/workflows/django.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Django 5.1](https://img.shields.io/badge/Django-5.1-success.svg)](https://www.djangoproject.com/)
[![REST API](https://img.shields.io/badge/REST%20API-OpenAPI%203.0-orange.svg)](http://localhost:8000/api/docs/)

AlzPredictor is a cloud-native, HIPAA-conscious medical diagnostic platform designed for early cognitive impairment screening, risk assessment, doctor consultations, and continuous machine learning model training.

---

## 🌟 Key Features

1. **AI Cognitive Risk Evaluation**:
   - Multi-factor algorithmic risk scoring (MMSE cognitive score, age, BMI, smoking, family history, physical activity).
   - Categorizes patient risk into **Normal**, **MCI (Mild Cognitive Impairment)**, and **Dementia** with statistical confidence bounds.
2. **Interactive 3D VR Spatial Memory Game**:
   - Browser-native WebGL / Three.js memory test.
   - Evaluates pathfinding latency and recall errors, automatically converting telemetry to the 30-point MMSE standard.
3. **Prescription Scanner & Drug Interaction Advisor**:
   - Extracts Alzheimer's medications (Donepezil, Memantine, Lecanemab) with clinical interaction analysis.
4. **Clinical Provider & Triage Workflow**:
   - Case review queue for doctors and nurses to annotate findings and schedule follow-ups.
5. **Continuous Model Training Telemetry**:
   - Management board supporting asynchronous retraining of Random Forest and Deep Learning MLP architectures with live telemetry progress charts.
6. **OpenAPI 3.0 / Swagger Documentation**:
   - Interactive Swagger UI (`/api/docs/`) and ReDoc (`/api/redoc/`) with JWT Bearer & Cookie authentication schemes.

---

## 🚀 Quick Start (Local Development)

### 1. Clone & Enter Directory
```bash
git clone https://github.com/mijanur531/alz_predictor.git
cd alz_predictor
```

### 2. Environment Setup (Windows / Linux)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (cmd):
call venv\Scripts\activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize Database & Seed Sample Data
```bash
# Run migrations
python manage.py migrate --settings=alz_predictor.settings.dev

# Seed verified doctors, patients, models, and predictions
python seed.py
```

### 4. Run Development Server
```bash
python manage.py runserver 0.0.0.0:8000 --settings=alz_predictor.settings.dev
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser!

---

## 🔑 Default Accounts (from `seed.py`)

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Patient** | `patient_alice` | `password123` | Patient Hub, Risk Assessments, 3D VR Test |
| **Doctor** | `doctor_house` | `password123` | Clinical Intake Board, Case Annotations |
| **Nurse** | `nurse_clara` | `password123` | Patient Triage & Vitals Monitoring |
| **Manager** | `manager` | `password123` | Management Analytics, ML Model Retraining |

---

## 🛡️ Security & Authentication

- **Dual-Layer Authentication**: Full support for both `Authorization: Bearer <token>` HTTP headers and secure HTTP cookies (`JWTCookieAuthentication`).
- **CSRF Protection**: Integrated with `CsrfViewMiddleware` and `CSRF_TRUSTED_ORIGINS` for single-page applications (React, Vite, Vue).
- **Public CSRF Endpoint**: `GET /api/v1/auth/csrf/` generates and sets `csrftoken` cookie.
- **Audit Logging**: Append-only audit trail (`management.models.AuditLog`) tracking logins, risk predictions, case reviews, and model deployments.

---

## 🧪 Testing & CI/CD

```bash
# Run the automated pytest suite (24 tests)
pytest api/tests.py -v
```

GitHub Actions pipeline (`.github/workflows/django.yml`) runs on every push:
- **Lint**: Flake8 critical syntax checks, Black, and isort.
- **Test**: Pytest with PostgreSQL and Redis services.
- **Security**: Bandit static vulnerability scans & Safety dependency audit.
- **Build**: Multi-stage Docker container packaging.

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
All libraries and resources used are 100% free and open-source.
