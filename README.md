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

## Deploy on Render

Official Render docs I used:

- [Deploy a Flask App on Render](https://render.com/docs/deploy-flask)
- [Web Services](https://render.com/docs/web-services)
- [Blueprint YAML Reference](https://render.com/docs/blueprint-spec)

This repo now includes `render.yaml` for a Render web service.

In Render:

1. Connect your GitHub account.
2. Create a new Blueprint or Web Service from this repository.
3. Set `ADMIN_PASSWORD` to a real secret value.
4. Deploy the `master` branch.

Render will install dependencies with `pip install -r requirements.txt` and start the app with `gunicorn app:app`.

Note:

- Render requires the app to listen on `0.0.0.0` and use the platform `PORT`, which is already configured in `app.py`.
- This app stores SQLite data and uploads on the service filesystem. On Render free instances, that storage is ephemeral, so database content and uploaded files can be lost on redeploy or restart. For durable storage, move the database to PostgreSQL and uploads to an object store.
