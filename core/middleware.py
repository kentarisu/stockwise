import json
from django.http import JsonResponse
from django.conf import settings

class JSONErrorMiddleware:
    """
    Middleware to ensure that requests to /api/ endpoints always return JSON responses,
    even for server errors (500) or client errors (400/403/404) that might otherwise
    render HTML error pages.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only handle API requests
        if request.path.startswith('/api/'):
            # If status code indicates an error (4xx or 5xx) and content type is not JSON
            if 400 <= response.status_code < 600:
                if 'application/json' not in response.get('Content-Type', ''):
                    # Try to extract error message from response content if possible
                    # otherwise use standard HTTP status phrases
                    message = 'An error occurred'
                    try:
                        # If response has content attribute and it's bytes/string
                        if hasattr(response, 'content'):
                            content = response.content.decode('utf-8')
                            # If it's the standard Django debug page or HTML error
                            if '<html' in content or '<!DOCTYPE' in content:
                                # Use a generic message for HTML errors to avoid leaking info
                                # unless in debug mode where we might want more info (optional)
                                message = f'Server Error ({response.status_code})'
                                if settings.DEBUG:
                                    message += '. Check server logs for details.'
                            else:
                                message = content[:200] # Use first 200 chars of non-HTML content
                    except Exception:
                        pass
                        
                    data = {
                        'success': False,
                        'message': message,
                        'status_code': response.status_code
                    }
                    return JsonResponse(data, status=response.status_code)
                    
        return response

    def process_exception(self, request, exception):
        """
        Catch unhandled exceptions for API requests and return JSON.
        """
        if request.path.startswith('/api/'):
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            
            # Log the full exception
            logger.error(f"API Error: {str(exception)}\n{traceback.format_exc()}")
            
            message = str(exception)
            if not settings.DEBUG:
                message = "An internal server error occurred."
            
            return JsonResponse({
                'success': False,
                'message': message
            }, status=500)
        return None
