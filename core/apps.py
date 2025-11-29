from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        import core.signals
        import os
        import threading
        try:
            _enabled = os.getenv('ENABLE_INTERNAL_SCHEDULER', 'true').lower() == 'true'
        except Exception:
            _enabled = True
        if _enabled:
            try:
                from sms_scheduler import SMSScheduler
                def _run():
                    try:
                        s = SMSScheduler()
                        s.run()
                    except Exception:
                        pass
                t = threading.Thread(target=_run, daemon=True)
                t.start()
            except Exception:
                pass
        try:
            from core.models import SMSNotificationSettings
            s = SMSNotificationSettings.get_settings()
            if (s.sales_time or '').strip() != '22:30':
                s.sales_time = '22:30'
                s.save()
        except Exception:
            pass
