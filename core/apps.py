from django.apps import AppConfig
from django.conf import settings


_SCHEDULER_STARTED = False

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        import core.signals
        import os
        import threading
        from django.core.signals import request_started
        try:
            _enabled = os.getenv('ENABLE_INTERNAL_SCHEDULER', 'false').lower() == 'true'
        except Exception:
            _enabled = False
        global _SCHEDULER_STARTED
        if _enabled and not _SCHEDULER_STARTED:
            def _start_scheduler_once(*args, **kwargs):
                global _SCHEDULER_STARTED
                if _SCHEDULER_STARTED:
                    return
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
                    _SCHEDULER_STARTED = True
                except Exception:
                    pass
                try:
                    request_started.disconnect(_start_scheduler_once)
                except Exception:
                    pass
            try:
                request_started.connect(_start_scheduler_once)
            except Exception:
                pass
