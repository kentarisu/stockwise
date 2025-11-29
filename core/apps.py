from django.apps import AppConfig
from django.conf import settings


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        import core.signals
        import os
        import threading
        try:
            _enabled = os.getenv('ENABLE_INTERNAL_SCHEDULER', 'false').lower() == 'true'
        except Exception:
            _enabled = False
        if _enabled and getattr(settings, 'DEBUG', True):
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
