# Backend — Django REST Framework API

Isolated Python project. Nothing here depends on the `frontend` folder.

## Project structure

```
backend/
├── config/          Project core: settings.py, urls.py (see PDF section 2)
├── users/           Custom User model (email login, role), auth endpoints, permissions
├── vehicles/        Vehicle inventory: Location, Vehicle models (PDF section 3.2)
├── requirements.txt
├── .env.example     Template — no real values, safe to commit
└── .env             Real local values — git-ignored, never commit
```

## Setup (first time)

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in real values (SECRET_KEY, PostgreSQL
   credentials — see the root README for why these are separated).
4. Make sure PostgreSQL is running and the database/user from `.env` exist
   (see `POSTGRES_DB` / `POSTGRES_USER` in `.env.example`).
5. Apply migrations and start the dev server:
   ```
   python manage.py migrate
   python manage.py runserver
   ```

## Auth endpoints

| Method | Endpoint             | Description                                   |
|--------|-----------------------|------------------------------------------------|
| POST   | `/api/auth/register`  | Create a new customer account                 |
| POST   | `/api/auth/login`     | Exchange email+password for access/refresh JWT |
| POST   | `/api/auth/refresh`   | Exchange a refresh token for a new access token|
| GET    | `/api/docs`           | Interactive Swagger UI for all endpoints       |

## Status

**Phase 2 — done.**

- Django 5 + DRF project (`config`) connected to PostgreSQL via env vars
  (no secrets in code — see `config/settings.py`).
- Custom `User` model (`users` app): email login, `role` field
  (customer/operator/admin).
- `Vehicle` / `Location` models (`vehicles` app), first migration applied.
- JWT auth (register/login/refresh) implemented and tested end-to-end.
- Role-based permission classes (`IsCustomer`, `IsOperator`, `IsAdmin`) in
  `users/permissions.py`, ready to be used once role-restricted endpoints
  (vehicle CRUD, reservations, etc.) are built.

Not yet done: vehicle search/CRUD API, reservations, everything past
Week 2 of the PDF plan.