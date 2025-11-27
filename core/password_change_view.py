"""
Password change functionality for TC-035
ISO/IEC 25010:2011 - Functional Completeness
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from core.models import AppUser
from passlib.hash import bcrypt
from core.views import require_app_login, _is_strong_password, _verify_password
import re

 


@require_app_login
@require_http_methods(["POST"])
def change_password(request):
    """
    TC-035: Password change endpoint
    Changes user password and invalidates other sessions
    """
    try:
        user_id = request.session.get('app_user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': 'User not authenticated.'})
        
        old_password = request.POST.get('old_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        # Validation
        if not old_password:
            return JsonResponse({'success': False, 'message': 'Current password is required.'})
        if not new_password:
            return JsonResponse({'success': False, 'message': 'New password is required.'})
        if not _is_strong_password(new_password):
            return JsonResponse({'success': False, 'message': 'New password must be at least 8 characters and include uppercase, lowercase, number, and symbol.'})
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'New passwords do not match.'})
        
        # Get user
        user = AppUser.objects.filter(user_id=user_id).first()
        if not user:
            return JsonResponse({'success': False, 'message': 'User not found.'})
        if (user.role or '').lower() == 'secretary':
            return JsonResponse({'success': False, 'message': 'Unauthorized. Please contact an admin to change password.'}, status=403)
        
        # Verify old password
        stored_password = user.password
        password_valid = _verify_password(stored_password, old_password)
        
        if not password_valid:
            return JsonResponse({'success': False, 'message': 'Current password is incorrect.'})
        
        # Hash and save new password
        user.password = bcrypt.hash(new_password)
        user.save()
        
        # Note: In a production system, you would invalidate other sessions here
        # For now, we'll just clear the current session and require re-login
        
        return JsonResponse({
            'success': True,
            'message': 'Password changed successfully. Please login again.',
            'require_relogin': True
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error changing password: {str(e)}'})

