from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

_SCHEDULER_STARTED = False

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        import core.signals
        import os
        import threading
        from django.core.signals import request_started
        from pathlib import Path
        
        # Auto-run migrations if needed (for hosting platforms without shell access)
        if os.getenv('AUTO_MIGRATE', 'false').lower() == 'true':
            try:
                from django.core.management import call_command
                logger.info("Running migrations automatically...")
                call_command('migrate', '--noinput')
                logger.info("Migrations completed successfully")
            except Exception as e:
                logger.error(f"Auto-migration failed: {e}")
        
        # Ensure media directories exist (create them if possible, ignore permission errors)
        try:
            media_root = Path(settings.MEDIA_ROOT)
            media_root.mkdir(parents=True, exist_ok=True)
            (media_root / 'builtins').mkdir(parents=True, exist_ok=True)
            (media_root / 'uploads').mkdir(parents=True, exist_ok=True)
            logger.info(f"Media directories ensured at {media_root}")
        except (PermissionError, OSError) as e:
            # In read-only filesystems (like some hosting platforms), this is expected
            logger.warning(f"Could not create media directories: {e}")
        
        # Verify SMS service configuration on startup
        try:
            from core.sms_service import sms_service
            logger.info(f"SMS Service ready - sender_name='{sms_service.sender_name}', api_token={'CONFIGURED' if sms_service.api_token else 'NOT CONFIGURED'}")
            if sms_service.sender_name != 'kaprets':
                logger.error(f"CRITICAL: SMS sender_name is '{sms_service.sender_name}' but should be 'kaprets'!")
        except Exception as e:
            logger.error(f"Error verifying SMS service: {e}", exc_info=True)
        
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
                            logger.info("Starting SMS scheduler in background thread...")
                            s = SMSScheduler()
                            s.run()
                        except Exception as e:
                            logger.error(f"Error in SMS scheduler: {e}", exc_info=True)
                    t = threading.Thread(target=_run, daemon=True, name="SMS_Scheduler")
                    t.start()
                    _SCHEDULER_STARTED = True
                    logger.info("SMS scheduler started successfully")
                except Exception as e:
                    logger.error(f"Failed to start SMS scheduler: {e}", exc_info=True)
                try:
                    request_started.disconnect(_start_scheduler_once)
                except Exception:
                    pass
            try:
                request_started.connect(_start_scheduler_once)
            except Exception:
                pass
        elif not _enabled:
            logger.info("SMS scheduler disabled. Set ENABLE_INTERNAL_SCHEDULER=true to enable.")
