# DGP Bus – Hospital Appointment & Transportation Manager

A Django REST API backend for managing hospital appointments, transportation scheduling, and user access. Designed for use by hospital staff and site personnel to coordinate patient visits, accommodation, and travel.

---

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Usage](#usage)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributors](#contributors)
- [License](#license)

---

## Introduction

**DGP Bus** is a RESTful API built with Django and Django REST Framework. It provides tools for managing:
- Staff and site user accounts (with role-based permissions)
- Patients and appointments
- Hospital transport scheduling
- Password reset and invite flows
- Smart bus time computation based on predefined schedules

This project is tailored for the **Greenlandic Patient Home system** and is localized in **Danish** (`da-DK`).

---

## Features

- JWT-based authentication with `SimpleJWT`
- Manage hospitals, schedules, patients, and appointments
- Auto-computation of departure/bus times
- User invitation and registration flows
- Password reset workflows
- Daily appointment queries & filters
- Admin/staff site support
- Celery + Redis for asynchronous tasks
- Danish locale and timezone support

---

## Installation

### 1. Clone the repo

```bash
git clone git@github.com:piitaaraq/dgpbus-back.git
cd dgpbus-back
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file:

```dotenv
DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=True
DJANGO_ENV=development

DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your@mailgun.org
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

CORS_ALLOWED_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=127.0.0.1,localhost
BASE_URL=http://localhost:8000
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Start the server

```bash
python manage.py runserver
```

---

## Configuration

- **Custom User Models:**
  - `StaffAdminUser` (admin/staff)
  - `SiteUser` (site-level restricted user)
- **Auth Backends:**
  - `dgp_bus.backends.SiteUserBackend`
- **Celery Tasks:**
  - Taxi email reporting
  - Expired entry cleanup

> See `settings.py` for Celery and JWT configuration.

---

## API Endpoints

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/api/hospitals/` | GET, POST | List or create hospitals |
| `/api/appointments/` | CRUD | Manage patient appointments |
| `/api/siteusers/register/` | POST | Register site user |
| `/api/token/` | POST | JWT login |
| `/api/token/refresh/` | POST | Refresh token |
| `/api/siteusers/password-reset-request/` | POST | Request reset |
| `/api/siteusers/invite/` | POST | Invite new user |
| `/api/patients/rides/today/` | GET | Today's rides grouped by time |
| `/api/appointments/public-taxi-users/` | GET | Anonymous view of taxi users |
| `/api/appointments/calculate-bus-time/` | POST | Compute bus departure time |

See the full list in `urls.py`.

---

## Authentication

- **JWT-based Auth**
  - Login: `/api/token/`
  - Refresh: `/api/token/refresh/`
- Admin/staff users use `StaffAdminUser`
- Regular site users use `SiteUser` with limited permissions

---

## 🧪 Usage

Sample login request:

```http
POST /api/token/
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

Sample appointment creation:

```http
POST /api/appointments/
Authorization: Bearer <your_token>
{
  "patient_id": 1,
  "hospital_id": 2,
  "accommodation_id": 5,
  "appointment_date": "2025-10-05",
  "appointment_time": "10:00"
}
```

> `bus_time_computed` will be automatically calculated if `bus_time_manual` is not provided.

---

## Examples

- **Find future appointments for a patient:**

```http
GET /api/appointments/find-patient/?name=John&room=203&accommodation=Det grønlandske Patienthjem
```

- **Toggle appointment status:**

```http
PATCH /api/appointments/{id}/toggle-status/
```

- **Calculate bus time manually:**

```http
POST /api/appointments/calculate-bus-time/
{
  "hospital_id": 1,
  "accommodation_id": 3,
  "appointment_date": "2025-10-01",
  "appointment_time": "11:30"
}
```

---

## Troubleshooting

- **Can't compute bus time?**
  - Make sure both hospital and accommodation are valid and support scheduling.

- **Users not active after registration?**
  - All users must be activated manually unless invited via admin.

- **.env not loading?**
  - Ensure `python-decouple` and `.env` file are correctly configured.

---

## Contributors

- **Primary Developer:** *Peter Løvstrøm*  
- **Email Integration:** Mailgun  
- **Task Queue:** Celery + Redis

---

## License

MIT License  
© 2025 Det grønlandske Patienthjem

