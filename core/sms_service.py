"""
SMS Service Module for iProg SMS API
Centralized SMS sending functionality for StockWise system
TC-028: SMS retry mechanism included
"""
import os
import requests
import time
from django.conf import settings


class IPROGSMSService:
    """SMS Service using iProg SMS API"""
    
    def __init__(self):
        """Initialize iProg SMS service with credentials"""
        self.api_token = os.getenv('IPROG_API_TOKEN') or getattr(settings, 'IPROG_API_TOKEN', None)
        self.api_url = 'https://sms.iprogtech.com/api/v1/sms_messages'
        self.sender_id = os.getenv('IPROG_SENDER_ID') or getattr(settings, 'IPROG_SENDER_ID', 'STOCKWISE')
        # Optional provider selector (0 or 1)
        try:
            self.sms_provider = int(os.getenv('IPROG_SMS_PROVIDER', getattr(settings, 'IPROG_SMS_PROVIDER', 0)))
        except Exception:
            self.sms_provider = 0
    
    def normalize_phone_number(self, phone_number):
        """
        Normalize phone number to iProg format (639xxxxxxxxx)
        
        Args:
            phone_number: Phone number in various formats
            
        Returns:
            Normalized phone number without + prefix
        """
        if not phone_number:
            return None
            
        # Remove common formatting characters
        normalized = phone_number.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Handle different formats
        if normalized.startswith('00'):
            # 00639xxxxxxxxx -> 639xxxxxxxxx
            normalized = normalized[2:]
        elif normalized.startswith('+63'):
            # +639xxxxxxxxx -> 639xxxxxxxxx
            normalized = normalized[1:]
        elif normalized.startswith('63'):
            # Already in correct format: 639xxxxxxxxx
            pass
        elif normalized.startswith('0'):
            # 09xxxxxxxxx -> 639xxxxxxxxx
            normalized = '63' + normalized[1:]
        elif normalized.startswith('9'):
            # 9xxxxxxxxx -> 639xxxxxxxxx
            normalized = '63' + normalized
        else:
            # Assume Philippines number without country code
            normalized = '63' + normalized
            
        return normalized
    
    def _to_gsm_plaintext(self, text: str, max_len: int | None = 160) -> str:
        """Convert message to GSM-7 friendly plain text.
        If max_len is provided, cap to that many characters; if None, do not truncate
        (allows multipart messages when needed).
        """
        if not text:
            return ''
        replacements = {
            '📊': 'Stats', '📅': 'Date', '💰': 'Revenue', '📦': 'Boxes', '🛒': 'Txns',
            '🏆': 'Top', '⚠️': 'Alert', '🚨': 'ALERT', '💡': 'Tip', '📈': 'Up', '📉': 'Down', '📱': 'StockWise'
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        text = ''.join(ch if ord(ch) < 128 else ' ' for ch in text)
        text = ' '.join(text.split())
        return text if max_len is None else text[:max_len]

    def send_sms(self, phone_number, message, allow_multipart: bool = False, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Send SMS using iProg SMS API with retry mechanism (TC-028)
        
        Args:
            phone_number: Recipient phone number
            message: SMS message content
            allow_multipart: Allow messages longer than 160 characters
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay in seconds between retries (default: 2.0)
            
        Returns:
            dict: Response with 'success' (bool) and 'message' (str)
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Wait before retry (exponential backoff)
                    wait_time = retry_delay * (2 ** (attempt - 1))
                    time.sleep(wait_time)
                
                # Check if API token is configured
                if not self.api_token:
                    return {
                        'success': False,
                        'message': 'iProg API token not configured. Please set IPROG_API_TOKEN in environment variables or Django settings.'
                    }
                
                # Normalize phone number
                normalized_phone = self.normalize_phone_number(phone_number)
                if not normalized_phone:
                    return {
                        'success': False,
                        'message': 'Invalid phone number provided'
                    }
                
                # Validate phone number format (should be 12 digits: 639xxxxxxxxx)
                if not normalized_phone.startswith('63') or len(normalized_phone) != 12:
                    return {
                        'success': False,
                        'message': f'Invalid phone number format: {normalized_phone}. Expected format: 639xxxxxxxxx'
                    }
                
                # Prepare API request using query parameters as per iProg documentation
                # For deliverability: keep to GSM-7; allow multi-part if requested
                max_len = None if allow_multipart else 160
                params = {
                    'api_token': self.api_token,
                    'phone_number': normalized_phone,
                    'message': self._to_gsm_plaintext(message, max_len=max_len),
                    'sms_provider': self.sms_provider
                }
                
                # Add custom sender_id if configured
                # Note: Custom sender ID must be registered and approved by iProg first
                # Contact iProg support to register "STOCKWISE" as your sender ID
                # Temporarily disabled until sender ID is approved
                # if self.sender_id:
                #     params['sender_id'] = self.sender_id
                
                # Send request to iProg API using query parameters
                response = requests.post(self.api_url, params=params, timeout=30)
                
                # Check response
                if response.status_code == 200:
                    response_data = response.json()
                    response_message = response_data.get('message', '')
                    
                    # Log the full API response for debugging (disabled in production)
                    # print(f"DEBUG: iProg API Response: {response_data}")
                    
                    # iProg API returns success with various messages
                    # Check for success indicators more strictly
                    if (response_data.get('status') == 'success' or 
                        response_data.get('status') == 200 or
                        response_data.get('success') is True or
                        'successfully added to the queue' in response_message.lower() or
                        'successfully sent' in response_message.lower() or
                        'message sent' in response_message.lower()):
                        return {
                            'success': True,
                            'message': f'SMS sent successfully to {normalized_phone} (attempt {attempt + 1})',
                            'api_response': response_message,
                            'response': response_data,
                            'message_code': response_data.get('message_id') or response_data.get('message_code') or response_data.get('id'),
                            'attempts': attempt + 1
                        }
                    else:
                        # Check for explicit failure indicators
                        if (response_data.get('status') == 'failed' or 
                            response_data.get('success') is False or
                            'failed' in response_message.lower() or
                            'error' in response_message.lower()):
                            last_error = {
                                'success': False,
                                'message': f'SMS failed to send: {response_message or "API returned failure status"}',
                                'api_response': response_message,
                                'response': response_data
                            }
                        else:
                            # Unknown response format - treat as failure for safety
                            last_error = {
                                'success': False,
                                'message': f'Unknown API response format. Message: {response_message or "No message"}',
                                'api_response': response_message,
                                'response': response_data
                            }
                        # Continue to next retry attempt
                        continue
                else:
                    last_error = {
                        'success': False,
                        'message': f'API request failed with status {response.status_code}: {response.text}'
                    }
                    # Continue to next retry attempt
                    continue
                    
            except requests.exceptions.RequestException as e:
                last_error = {
                    'success': False,
                    'message': f'Network error: {str(e)}'
                }
                # Continue to next retry attempt for network errors
                continue
            except Exception as e:
                last_error = {
                    'success': False,
                    'message': f'Error sending SMS: {str(e)}'
                }
                # Continue to next retry attempt
                continue
        
        # All retries failed
        if last_error:
            last_error['attempts'] = max_retries
            last_error['message'] = f"{last_error['message']} (failed after {max_retries} attempts)"
            return last_error
        else:
            return {
                'success': False,
                'message': f'Failed to send SMS after {max_retries} attempts',
                'attempts': max_retries
            }
    
    def check_sms_status(self, message_code):
        """
        Check the status of a sent SMS message
        
        Args:
            message_code: The message code returned from send_sms
            
        Returns:
            dict: Response with 'success' (bool), 'status' (str), and 'message' (str)
        """
        try:
            if not self.api_token:
                return {
                    'success': False,
                    'message': 'iProg API token not configured'
                }
            
            # Prepare API request for status check
            payload = {
                'api_token': self.api_token,
                'message_code': message_code
            }
            
            # Send request to iProg API status endpoint
            status_url = 'https://sms.iprogtech.com/api/v1/sms_status'
            response = requests.post(status_url, data=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                status = response_data.get('status', 'unknown')
                return {
                    'success': True,
                    'status': status,
                    'message': f'SMS status: {status}',
                    'response': response_data
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to check SMS status: {response.status_code} - {response.text}'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Network error checking SMS status: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error checking SMS status: {str(e)}'
            }

    def check_credits(self):
        """
        Check remaining SMS credits (if supported by iProg API)
        
        Returns:
            dict: Response with credit information
        """
        try:
            if not self.api_token:
                return {
                    'success': False,
                    'message': 'iProg API token not configured'
                }
            
            # iProg may have a credits endpoint - adjust URL if needed
            credits_url = 'https://sms.iprogtech.com/api/v1/check_credits'
            payload = {'api_token': self.api_token}
            
            response = requests.post(credits_url, data=payload, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to check credits: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error checking credits: {str(e)}'
            }


# Singleton instance for easy importing
sms_service = IPROGSMSService()


def send_sms(phone_number, message, allow_multipart: bool = False):
    """
    Convenience function to send SMS
    
    Usage:
        from core.sms_service import send_sms
        result = send_sms('+639123456789', 'Hello from StockWise!')
        if result['success']:
            print('SMS sent successfully')
        else:
            print(f'Failed: {result["message"]}')
    """
    return sms_service.send_sms(phone_number, message, allow_multipart=allow_multipart)

