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
        # NOTE: IPROG SMS does not support custom sender IDs - all messages use system sender route
        # Keeping this for future when custom sender IDs are supported
        self.sender_id = os.getenv('IPROG_SENDER_ID') or getattr(settings, 'IPROG_SENDER_ID', 'PHILSMS')
        # App display name (used in message content, not sender ID)
        self.app_name = 'STOCKWISE'
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
        Removes Unicode characters to avoid telco delivery issues.
        
        IMPORTANT: IPROG SMS rejects Unicode/special characters:
        - Replace peso sign (₱) with "PHP"
        - Remove emojis, smart quotes, Unicode symbols
        - Use only GSM-7 compatible characters
        
        If max_len is provided, cap to that many characters; if None, do not truncate
        (allows multipart messages when needed).
        """
        if not text:
            return ''
        
        # Replace common Unicode characters with plain text equivalents
        replacements = {
            # Currency symbols
            '₱': 'PHP ', '₽': 'PHP ', '€': 'EUR ', '£': 'GBP ', '$': 'USD ',
            
            # Emojis (if any slip through)
            '📊': 'Stats', '📅': 'Date', '💰': 'Revenue', '📦': 'Boxes', '🛒': 'Txns',
            '🏆': 'Top', '⚠️': 'Alert', '🚨': 'ALERT', '💡': 'Tip', '📈': 'Up', '📉': 'Down', 
            '📱': 'STOCKWISE', '❤️': '', '™': '', '®': '', '©': '',
            
            # Smart quotes and punctuation
            '"': '"', '"': '"', ''': "'", ''': "'", '—': '-', '–': '-',
            '…': '...',
        }
        
        for k, v in replacements.items():
            text = text.replace(k, v)
        
        # Remove any remaining non-ASCII characters (except newlines)
        text = ''.join(ch if ord(ch) < 128 or ch == '\n' else ' ' for ch in text)
        
        # Clean up extra whitespace but preserve line breaks
        lines = text.split('\n')
        cleaned_lines = [' '.join(line.split()) for line in lines]
        text = '\n'.join(cleaned_lines)
        
        return text if max_len is None else text[:max_len]

    def _submit_iprog(self, phone_number: str, text: str):
        """Helper: submit SMS to iProg and return its response dict (no client-side truncation)."""
        params = {
            'api_token': self.api_token,
            'phone_number': phone_number,
            'message': self._to_gsm_plaintext(text, max_len=None),
            'sms_provider': self.sms_provider
        }
        response = requests.post(self.api_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            msg = data.get('message', '')
            ok = (
                data.get('status') in ('success', 200)
                or data.get('success') is True
                or 'successfully' in msg.lower()
            )
            return ok, data
        return False, {'status_code': response.status_code, 'text': response.text}

    def send_sms(self, phone_number, message, allow_multipart: bool = False, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Send SMS using iProg SMS API.
        Implements manual concatenation when ``allow_multipart`` is True by splitting
        the cleaned GSM-7 text into 153-character segments (concatenation header safe).
        """
        if not message:
            return {'success': False, 'message': 'Empty message'}

        # --- Pre-flight validation shared across all segments ---
        if not self.api_token:
            return {'success': False, 'message': 'iProg API token not configured'}

        normalized_phone = self.normalize_phone_number(phone_number)
        if not normalized_phone or not normalized_phone.startswith('63') or len(normalized_phone) != 12:
            return {'success': False, 'message': f'Invalid phone number: {phone_number}'}

        # Clean & optionally segment message
        clean_text = self._to_gsm_plaintext(message, max_len=None)
        if allow_multipart:
            segment_len = 153  # 153 for UDH concatenation header space
            segments = [clean_text[i:i+segment_len] for i in range(0, len(clean_text), segment_len)]
        else:
            # Do not split; send as a single payload
            segments = [clean_text]

        results = []
        part_count = len(segments)
        for idx, seg in enumerate(segments, start=1):
            # Optional prefix only when multipart
            seg_payload = seg

            last_error = None
            for attempt in range(max_retries):
                if attempt:
                    time.sleep(retry_delay * (2 ** (attempt - 1)))
                try:
                    ok, data = self._submit_iprog(normalized_phone, seg_payload)
                    if ok:
                        results.append({'success': True, 'response': data})
                        break
                    else:
                        last_error = data
                        continue
                except requests.exceptions.RequestException as e:
                    last_error = {'success': False, 'message': f'Network error: {e}'}
                    continue
                except Exception as e:
                    last_error = {'success': False, 'message': str(e)}
                    continue
            else:
                # Exhausted retries for this segment
                results.append(last_error or {'success': False, 'message': 'Unknown error'})

        all_ok = all(r.get('success') for r in results)
        if all_ok:
            codes = [str(r.get('response', {}).get('message_id') or r.get('response', {}).get('id') or '') for r in results]
            return {
                'success': True,
                'message': f'Sent {len(results)} SMS segment(s) successfully',
                'message_code': ','.join([c for c in codes if c]),
                'responses': results,
            }
        return {
            'success': False,
            'message': 'One or more segments failed',
            'responses': results,
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
            
            # Prepare API request for status check (use official status endpoint)
            # iProg provides a message status link like:
            #   https://sms.iprogtech.com/api/v1/sms_messages/status?api_token=...&message_id=...
            params = {
                'api_token': self.api_token,
                'message_id': message_code
            }
            status_url = 'https://sms.iprogtech.com/api/v1/sms_messages/status'
            response = requests.get(status_url, params=params, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                status = response_data.get('message_status', response_data.get('status', 'unknown'))
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
