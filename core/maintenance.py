"""
Maintenance Mode Middleware and Helper for TC-043
ISO/IEC 25010:2011 - Portability (Adaptability/Installability)
"""
from django.http import HttpResponse
from django.conf import settings
import os


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

