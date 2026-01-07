"""
Maintenance Mode Middleware and Helper for TC-043
ISO/IEC 25010:2011 - Portability (Adaptability/Installability)
"""
from django.http import HttpResponse
from django.conf import settings
import os
import json
import time


def is_maintenance_mode():
    """
    Check if the system is in maintenance mode
    Checks both environment variable and settings
    """
    return (
        os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true' or
        getattr(settings, 'MAINTENANCE_MODE', False)
    )


class MaintenanceModeMiddleware:
    """
    Middleware to enable maintenance mode for the entire application
    TC-043: Graceful degradation during updates/maintenance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Check if maintenance mode is enabled
        if is_maintenance_mode():
            # Allow access to admin panel even during maintenance
            if request.path.startswith('/admin/'):
                return self.get_response(request)
            
            # Return maintenance page for all other requests
            return self.maintenance_response()
        
        return self.get_response(request)
    
    def maintenance_response(self):
        """Return a maintenance mode response"""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>System Maintenance - StockWise</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                }
                .container {
                    background: white;
                    padding: 3rem 2rem;
                    border-radius: 12px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    max-width: 500px;
                    text-align: center;
                }
                h1 {
                    color: #667eea;
                    margin-bottom: 1rem;
                    font-size: 2rem;
                }
                p {
                    color: #666;
                    line-height: 1.6;
                    margin-bottom: 1rem;
                }
                .icon {
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }
                .status {
                    background: #f0f4ff;
                    padding: 1rem;
                    border-radius: 8px;
                    margin-top: 1.5rem;
                }
                .status-text {
                    color: #667eea;
                    font-weight: 600;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">🔧</div>
                <h1>System Maintenance</h1>
                <p>StockWise is currently undergoing scheduled maintenance to improve your experience.</p>
                <p>We'll be back online shortly. Thank you for your patience!</p>
                <div class="status">
                    <p class="status-text">Estimated downtime: 10-30 minutes</p>
                </div>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html, status=503)


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_ts = time.time()
        response = None
        try:
            response = self.get_response(request)
            return response
        finally:
            try:
                if not getattr(settings, 'AUDIT_MIDDLEWARE_ENABLED', False):
                    pass
                path = request.path or ''
                method = (request.method or '').upper()
                role = (request.session.get('app_role') or '').strip()
                action = f"{method} {path}"
                params = {}
                try:
                    if request.GET:
                        params['query'] = {k: request.GET.get(k, '') for k in request.GET.keys()}
                except Exception:
                    pass
                body = {}
                try:
                    if request.META.get('CONTENT_TYPE', '').lower().startswith('application/json'):
                        import json as _json
                        parsed = _json.loads(request.body.decode('utf-8') or '{}') if request.body else {}
                        body = parsed if isinstance(parsed, dict) else {'_raw': str(parsed)}
                    elif request.POST:
                        body = {k: request.POST.get(k, '') for k in request.POST.keys()}
                except Exception:
                    pass
                redacted_keys = {'password', 'new_password', 'confirm_password', 'token', 'authorization', 'csrfmiddlewaretoken', 'csrf_token'}
                def _redact(d):
                    out = {}
                    for k, v in (d or {}).items():
                        if str(k).lower() in redacted_keys:
                            out[k] = '[REDACTED]'
                        else:
                            out[k] = v
                    return out
                details_obj = {
                    'role': role,
                    'status_code': getattr(response, 'status_code', None),
                    'duration_ms': int((time.time() - start_ts) * 1000),
                    'query': _redact(params.get('query') or {}),
                    'body': _redact(body),
                    'referer': request.META.get('HTTP_REFERER', ''),
                }
                p = (path or '').lower()
                excluded_fragments = (
                    '/sms-settings/',
                    '/api/sms/settings',
                    '/api/sms/test',
                    '/api/sms/',
                )
                should_log = (
                    getattr(settings, 'AUDIT_MIDDLEWARE_ENABLED', False) and
                    not p.startswith('/static/') and
                    not p.startswith('/media/') and
                    not p.startswith('/uploads/') and
                    method not in ('GET', 'HEAD', 'OPTIONS') and
                    all(frag not in p for frag in excluded_fragments)
                )
                if should_log:
                    from core.views import log_action
                    log_action(request, action, json.dumps(details_obj))
            except Exception:
                pass

    def process_exception(self, request, exception):
        try:
            if not getattr(settings, 'AUDIT_MIDDLEWARE_ENABLED', False):
                return None
            from django.http import Http404
            path = request.path or ''
            p = (path or '').lower()
            if p.startswith('/static/') or p.startswith('/media/') or p.startswith('/uploads/'):
                return None
            method = (request.method or '').upper()
            if method in ('GET', 'HEAD', 'OPTIONS'):
                return None
            if ('/sms-settings/' in p) or ('/api/sms/' in p):
                return None
            if isinstance(exception, Http404):
                return None
            action = f"{method} {path} (exception)"
            details_obj = {
                'error': str(exception),
            }
            from core.views import log_action
            log_action(request, action, json.dumps(details_obj))
        except Exception:
            pass
        return None


class FriendlyErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        try:
            from django.http import JsonResponse, HttpResponse
            from django.utils import timezone
            import html
            # Check if this is an API/AJAX request
            path = (request.path or '').lower()
            accepts_json = (
                'application/json' in (request.META.get('HTTP_ACCEPT', '') or '').lower() or
                request.headers.get('x-requested-with', '').lower() == 'xmlhttprequest' or
                path.startswith('/api/') or
                'backup' in path or  # Backup endpoints should always return JSON
                'pricing' in path or  # Pricing API endpoints
                'sms' in path  # SMS API endpoints
            )
            err_id = timezone.now().strftime('%Y%m%d%H%M%S')
            msg = 'Something went wrong. Please try again or refresh the page.'
            details = 'If the problem persists, check Logs for details.'
            if accepts_json:
                return JsonResponse({
                    'success': False,
                    'message': msg,
                    'error_id': err_id
                }, status=500)
            safe = html.escape(str(exception))
            html_body = f"""
            <!DOCTYPE html>
            <html lang=\"en\">
            <head>
              <meta charset=\"utf-8\">
              <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
              <title>StockWise – Error</title>
              <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\">
            </head>
            <body class=\"bg-light\">
              <div class=\"container py-5\">
                <div class=\"alert alert-danger\">
                  <i class=\"bi bi-exclamation-triangle me-2\"></i>
                  {msg}
                  <div class=\"small text-muted mt-2\">Error ID: {err_id}</div>
                </div>
                <div class=\"card\">
                  <div class=\"card-body\">
                    <div class=\"mb-2\">{details}</div>
                    <div class=\"small text-muted\">Technical info: {safe}</div>
                    <a href=\"/logs\" class=\"btn btn-outline-secondary btn-sm mt-3\">View Logs</a>
                    <a href=\"/\" class=\"btn btn-primary btn-sm mt-3 ms-2\">Go to Dashboard</a>
                  </div>
                </div>
              </div>
              <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js\"></script>
            </body>
            </html>
            """
            return HttpResponse(html_body, status=500)
        except Exception:
            return None

