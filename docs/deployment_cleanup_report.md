# Deployment Cleanup Report (2025-11-27)

## Overview
- Performed full inventory scan and removed non-production artifacts.
- Verified Django app health, migrations, and static collection.
- Pruned test-only dependencies from requirements.

## Key Components
- Project settings: `stockwise_py/settings.py`
- Django apps: `core`, `stockwise_qr.qrstock`
- Entrypoint: `manage.py` using `stockwise_py.settings`
- Templates: `templates/` and `stockwise_qr/qrstock/templates/`
- Static dirs: `static/`, `stockwise_py/static/` → collected to `staticfiles/`

## Removed Items
- Directories: `core/tests`, `config/`, `includes/`, `lib/`, `stockwise_django/`
- Files: `.coverage`, `ISO25010_TEST_RESULTS.csv`, `IPROG_SENDER_ID_REQUEST.txt`, `IPROG_SENDER_ID_REQUEST_SHORT.txt`, `SAMPLE SPREADSHEET.xlsx`, `fruitmaster dummy data.csv`, `fruitmaster.csv`, `gaa.csv`, `data_dictionary.html`, `client_secret_2_*.json`, `db.sqlite3.backup_temp_restore_*`, `ngrok.zip`, `ngrok_v3.zip`, `download_ngrok.ps1`, `auto_setup_ngrok.bat`, `setup_ngrok.bat`, `start_ngrok.bat`, `check_windows_printers.py`, `list_com_ports.py`, `qrsourcecode.py`

## Dependency Changes
- Removed dev/test packages from `requirements.txt`: `pytest`, `pytest-django`, `pytest-cov`, `factory-boy`.
- Retained production packages: `Django`, `whitenoise`, `gunicorn`, `dj-database-url`, `psycopg2-binary`, `numpy`, `pandas`, `python-escpos`, `pyserial`, `pywin32`, `google-auth`, `requests`, `python-dotenv`, `passlib`, `reportlab`, `django-crontab`.

## Verification
- `manage.py check`: no issues.
- `manage.py migrate`: up-to-date.
- `manage.py collectstatic --noinput`: copied 3 files, 128 unmodified (duplicate names in `css/js` noted by collector).

## Notes
- Ngrok tooling removed; production should expose via standard ingress/reverse proxy.
- Backups under `backups/` kept; temporary restore artifacts removed.
- Duplicate static filenames exist (`modern-inventory.css`, `modern-inventory.js`) in multiple dirs; first occurrence is collected. Standardization can further reduce redundancy.

## Current Structure (essentials)
- Apps: `core`, `stockwise_qr/qrstock`
- Settings: `stockwise_py/settings.py`
- Templates: `templates/*`, `stockwise_qr/qrstock/templates/*`
- Static roots: `static/`, `stockwise_py/static/`, collected to `staticfiles/`
- Scripts: `sms_scheduler.py`, printer setup `setup_thermal_printer.py`

## Next Recommendations
- Configure `DEBUG=False`, tighten `ALLOWED_HOSTS`, enable `SECURE_SSL_REDIRECT` on production.
- Move secrets to environment; rotate hardcoded `SECRET_KEY` and API tokens.
- Consider merging duplicate static assets and pruning unused templates after usage audit.
