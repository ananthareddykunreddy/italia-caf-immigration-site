# Italia CAF Immigration Site

Flask-based multi-page website project for a business in Italy offering:

- CAF services
- Immigration consulting
- Student admission support
- Indian Embassy support services

## Features

- Multi-page website with shared layout and service pages
- Appointment booking form
- SQLite database for saved appointment records
- File uploads stored on the server
- Admin login and dashboard for reviewing records
- Embassy support sections for:
  - Passport application assistance
  - OCI card application assistance
  - Passport surrender assistance

## Run locally

```powershell
cd C:\Users\anant\OneDrive\Documents\Playground\italia-caf-immigration-site
$env:ADMIN_PASSWORD="change-me-now"
python run_local.py
```

Then open:

- `http://localhost:8000/`
- `http://localhost:8000/appointments`
- `http://localhost:8000/admin/login`

## Admin access

- Default admin password fallback: `change-me-now`
- Set `ADMIN_PASSWORD` in the shell before running for a safer local setup

## Project structure

- `app.py` Flask entry point
- `templates/` multi-page Jinja templates
- `static/styles.css` shared styling
- `data/site.db` SQLite database created at runtime
- `uploads/` client file uploads
