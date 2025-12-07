web: gunicorn stockwise_py.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
worker: python sms_scheduler.py
