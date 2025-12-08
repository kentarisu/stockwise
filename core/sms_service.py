"""
SMS Service Module for iProg SMS API
Centralized SMS sending functionality for StockWise system
TC-028: SMS retry mechanism included
"""
import os
import requests
import time
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class IPROGSMSService:
    """SMS Service using iProg SMS API"""
    
    def __init__(self):
        """Initialize iProg SMS service with credentials"""
        self.api_token = os.getenv('IPROG_API_TOKEN') or getattr(settings, 'IPROG_API_TOKEN', None)
        self.api_url = 'https://sms.iprogtech.com/api/v1/sms_messages'
        # NOTE: IPROG SMS does not support custom sender IDs - all messages use system sender route
        # Keeping this for future when custom sender IDs are supported
        self.sender_id = os.getenv('IPROG_SENDER_ID') or getattr(settings, 'IPROG_SENDER_ID', 'PHILSMS')
        # Main sender name for all SMS notifications (daily sales, stock alerts, pricing recommendations)
        # Always set to "kaprets" as per requirements - ENFORCED
        sender_name_env = os.getenv('IPROG_SENDER_NAME') or getattr(settings, 'IPROG_SENDER_NAME', None)
        self.sender_name = 'kaprets'  # Always use 'kaprets' regardless of settings
        if sender_name_env and sender_name_env.lower() != 'kaprets':
            logger.warning(f"IPROG_SENDER_NAME setting ({sender_name_env}) ignored. Using 'kaprets' as required.")
        # App display name (used in message content, not sender ID)
        self.app_name = 'STOCKWISE'
        # Optional provider selector (0 or 1)
        try:
            self.sms_provider = int(os.getenv('IPROG_SMS_PROVIDER', getattr(settings, 'IPROG_SMS_PROVIDER', 0)))
        except Exception:
            self.sms_provider = 0
        
        # Log configuration on initialization
        logger.info(f"SMS Service initialized with sender_name='{self.sender_name}', api_token={'CONFIGURED' if self.api_token else 'NOT CONFIGURED'}")
    
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
        
        # Prepare parameters - ENSURE sender_name is always 'kaprets'
        params_data = {
            'api_token': self.api_token,
            'phone_number': phone_number,
            'message': self._to_gsm_plaintext(text, max_len=None),
            'sender_name': 'kaprets'  # ALWAYS use 'kaprets' - enforced for all automated/scheduled SMS
        }
        # Double-check: Log and verify sender_name
        if params_data['sender_name'] != 'kaprets':
            logger.error(f"CRITICAL: sender_name is '{params_data['sender_name']}' instead of 'kaprets'!")
            params_data['sender_name'] = 'kaprets'  # Force correct value
        logger.debug(f"Sending SMS with sender_name='{params_data['sender_name']}', phone={phone_number[:5]}***")
        
        # Try multiple API endpoint formats and request methods
        # iProg API typically uses: https://sms.iprogtech.com/api/v1/sms_messages
        urls = [
            self.api_url,  # Primary: https://sms.iprogtech.com/api/v1/sms_messages
            'https://www.iprogsms.com/api/v1/sms_messages',
        ]
        
        last_error = None
        for url in urls:
            # Try GET request with query parameters (some SMS APIs use GET)
            try:
                logger.info(f"Attempting SMS send to {url} with GET request")
                response = requests.get(url, params=params_data, timeout=30)
                logger.info(f"GET Response status: {response.status_code}, body: {response.text[:200]}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except:
                        data = {'status': 'unknown', 'message': response.text}
                    
                    msg = str(data.get('message', '')).lower()
                    status_val = data.get('status')
                    success_val = data.get('success')
                    
                    ok = (
                        status_val in ('success', 200, 'ok', 'sent', 'delivered', 'queued')
                        or success_val is True
                        or success_val == 'true'
                        or 'successfully' in msg
                        or 'sent' in msg
                        or 'queued' in msg
                    )
                    
                    if ok:
                        logger.info(f"SMS sent successfully via {url} (GET): {data}")
                        return True, data
                    
                    last_error = {'url': url, 'response': data, 'method': 'get'}
                    logger.warning(f"SMS send failed via {url} (GET): {data}")
            except Exception as e:
                logger.error(f"Exception sending SMS to {url} (GET): {e}")
            
            # Try as query parameters first (most common for POST)
            try:
                logger.info(f"Attempting SMS send to {url} with query params")
                response = requests.post(url, params=params_data, timeout=30)
                logger.info(f"Response status: {response.status_code}, body: {response.text[:200]}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except:
                        data = {'status': 'unknown', 'message': response.text}
                    
                    msg = str(data.get('message', '')).lower()
                    status_val = data.get('status')
                    success_val = data.get('success')
                    
                    # Check multiple success indicators
                    ok = (
                        status_val in ('success', 200, 'ok', 'sent', 'delivered', 'queued')
                        or success_val is True
                        or success_val == 'true'
                        or 'successfully' in msg
                        or 'sent' in msg
                        or 'queued' in msg
                    )
                    
                    if ok:
                        logger.info(f"SMS sent successfully via {url}: {data}")
                        return True, data
                    
                    last_error = {'url': url, 'response': data, 'method': 'query_params'}
                    logger.warning(f"SMS send failed via {url} (query params): {data}")
                    continue
                else:
                    last_error = {'url': url, 'status_code': response.status_code, 'text': response.text[:500], 'method': 'query_params'}
                    logger.warning(f"SMS send failed via {url}: {response.status_code} - {response.text[:200]}")
            except Exception as e:
                logger.error(f"Exception sending SMS to {url} (query params): {e}")
                last_error = {'url': url, 'error': str(e), 'method': 'query_params'}
            
            # Try as form data (POST body)
            try:
                logger.info(f"Attempting SMS send to {url} with form data")
                response = requests.post(url, data=params_data, timeout=30)
                logger.info(f"Response status: {response.status_code}, body: {response.text[:200]}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except:
                        data = {'status': 'unknown', 'message': response.text}
                    
                    msg = str(data.get('message', '')).lower()
                    status_val = data.get('status')
                    success_val = data.get('success')
                    
                    ok = (
                        status_val in ('success', 200, 'ok', 'sent', 'delivered', 'queued')
                        or success_val is True
                        or success_val == 'true'
                        or 'successfully' in msg
                        or 'sent' in msg
                        or 'queued' in msg
                    )
                    
                    if ok:
                        logger.info(f"SMS sent successfully via {url} (form data): {data}")
                        return True, data
                    
                    last_error = {'url': url, 'response': data, 'method': 'form_data'}
                    logger.warning(f"SMS send failed via {url} (form data): {data}")
                    continue
                else:
                    last_error = {'url': url, 'status_code': response.status_code, 'text': response.text[:500], 'method': 'form_data'}
                    logger.warning(f"SMS send failed via {url} (form data): {response.status_code} - {response.text[:200]}")
            except Exception as e:
                logger.error(f"Exception sending SMS to {url} (form data): {e}")
                last_error = {'url': url, 'error': str(e), 'method': 'form_data'}
            
            # Try as JSON data (POST body)
            try:
                logger.info(f"Attempting SMS send to {url} with JSON data")
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, json=params_data, headers=headers, timeout=30)
                logger.info(f"Response status: {response.status_code}, body: {response.text[:200]}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except:
                        data = {'status': 'unknown', 'message': response.text}
                    
                    msg = str(data.get('message', '')).lower()
                    status_val = data.get('status')
                    success_val = data.get('success')
                    
                    ok = (
                        status_val in ('success', 200, 'ok', 'sent', 'delivered', 'queued')
                        or success_val is True
                        or success_val == 'true'
                        or 'successfully' in msg
                        or 'sent' in msg
                        or 'queued' in msg
                    )
                    
                    if ok:
                        logger.info(f"SMS sent successfully via {url} (JSON): {data}")
                        return True, data
                    
                    last_error = {'url': url, 'response': data, 'method': 'json'}
                    logger.warning(f"SMS send failed via {url} (JSON): {data}")
            except Exception as e:
                logger.error(f"Exception sending SMS to {url} (JSON): {e}")
                if not last_error or 'response' not in last_error:
                    last_error = {'url': url, 'error': str(e), 'method': 'json'}
        
        logger.error(f"All SMS send attempts failed. Last error: {last_error}")
        return False, last_error or {'success': False, 'message': 'Unknown error - all API endpoints failed'}

    def send_sms(self, phone_number, message, allow_multipart: bool = False, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Send SMS using iProg SMS API.
        Automatically splits into multipart with 1/2, 2/2 prefixes if message is too long (>160 chars).
        If allow_multipart is True, allows splitting. Otherwise, only splits if message exceeds single SMS limit.
        """
        if not message:
            logger.error("SMS send failed: Empty message")
            return {'success': False, 'message': 'Empty message'}

        # --- Pre-flight validation shared across all segments ---
        if not self.api_token:
            logger.error("SMS send failed: iProg API token not configured")
            return {'success': False, 'message': 'iProg API token not configured'}
        
        logger.info(f"Attempting to send SMS to {phone_number} with sender_name='{self.sender_name}', api_token={'*' * 10 if self.api_token else 'NONE'}")

        normalized_phone = self.normalize_phone_number(phone_number)
        if (not normalized_phone) or (not normalized_phone.startswith('63')) or (len(normalized_phone) not in (11, 12)):
            logger.error(f"SMS send failed: Invalid phone number format: {phone_number} -> {normalized_phone}")
            return {'success': False, 'message': f'Invalid phone number: {phone_number}'}
        
        logger.info(f"Normalized phone: {normalized_phone}")

        # Clean message first
        clean_text = self._to_gsm_plaintext(message, max_len=None)
        
        # Determine if we need multipart (only if message is TOO LONG)
        SINGLE_SMS_LIMIT = 160  # Standard SMS character limit
        
        # Check if message is too long and needs multipart
        if len(clean_text) > SINGLE_SMS_LIMIT and allow_multipart:
            # Use the unified formatter's split function for consistent formatting with 1/2, 2/2 prefixes
            from core.sms_formatter import split_long_message
            segments = split_long_message(clean_text, max_length=SINGLE_SMS_LIMIT)
        else:
            # Send as single message (even if slightly over limit if allow_multipart is False)
            segments = [clean_text]

        results = []
        part_count = len(segments)
        logger.info(f"Sending {part_count} SMS segment(s)")
        
        for idx, seg in enumerate(segments, start=1):
            seg_payload = seg
            logger.info(f"Sending segment {idx}/{part_count}, length: {len(seg_payload)} chars")

            last_error = None
            for attempt in range(max_retries):
                if attempt:
                    wait_time = retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay")
                    time.sleep(wait_time)
                try:
                    ok, data = self._submit_iprog(normalized_phone, seg_payload)
                    if ok:
                        logger.info(f"Segment {idx}/{part_count} sent successfully: {data}")
                        results.append({'success': True, 'response': data})
                        break
                    else:
                        last_error = data
                        logger.warning(f"Segment {idx}/{part_count} failed (attempt {attempt + 1}): {data}")
                        continue
                except requests.exceptions.RequestException as e:
                    last_error = {'success': False, 'message': f'Network error: {e}'}
                    logger.error(f"Network error sending segment {idx}/{part_count}: {e}")
                    continue
                except Exception as e:
                    last_error = {'success': False, 'message': str(e)}
                    logger.error(f"Exception sending segment {idx}/{part_count}: {e}", exc_info=True)
                    continue
            else:
                # Exhausted retries for this segment
                logger.error(f"Segment {idx}/{part_count} failed after {max_retries} attempts: {last_error}")
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

    def schedule_sms_reminder(self, phone_number: str, message: str, scheduled_at: str):
        """
        Schedule SMS reminder using iProg API.
        Format: POST with JSON body or query parameters
        """
        try:
            if not self.api_token:
                logger.error("iProg API token not configured")
                return {'success': False, 'message': 'iProg API token not configured'}
            
            normalized_phone = self.normalize_phone_number(phone_number)
            if (not normalized_phone) or (not normalized_phone.startswith('63')) or (len(normalized_phone) not in (11, 12)):
                logger.error(f"Invalid phone number: {phone_number} -> {normalized_phone}")
                return {'success': False, 'message': f'Invalid phone number: {phone_number}'}
            
            # Format: "2025-03-08 05:00AM" - ensure proper format
            # Remove any spaces and format correctly
            scheduled_at_clean = scheduled_at.strip()
            
            url = 'https://www.iprogsms.com/api/v1/message-reminders'
            
            # Try JSON body first (as per API documentation)
            json_data = {
                'api_token': self.api_token,
                'phone_number': normalized_phone,
                'scheduled_at': scheduled_at_clean,
                'message': self._to_gsm_plaintext(message, max_len=None)
            }
            
            logger.info(f"Scheduling SMS reminder via iProg API: phone={normalized_phone[:5]}***, scheduled_at={scheduled_at_clean}")
            
            headers = {'Content-Type': 'application/json'}
            resp = requests.post(url, json=json_data, headers=headers, timeout=30)
            
            logger.info(f"iProg API response: status={resp.status_code}, body={resp.text[:200]}")
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except:
                    data = {'status': 'unknown', 'message': resp.text}
                
                ok = (
                    data.get('status') == 'success' 
                    or data.get('success') is True
                    or 'success' in str(data.get('message', '')).lower()
                )
                
                if ok:
                    logger.info(f"SMS reminder scheduled successfully: {data}")
                    return {'success': True, 'response': data, 'message': data.get('message', 'Scheduled successfully')}
                else:
                    logger.warning(f"SMS reminder API returned non-success: {data}")
            
            # Try query parameters as fallback
            logger.info("Trying query parameters as fallback...")
            params = {
                'api_token': self.api_token,
                'phone_number': normalized_phone,
                'scheduled_at': scheduled_at_clean,
                'message': self._to_gsm_plaintext(message, max_len=None)
            }
            resp2 = requests.post(url, params=params, timeout=30)
            logger.info(f"iProg API response (query params): status={resp2.status_code}, body={resp2.text[:200]}")
            
            if resp2.status_code == 200:
                try:
                    data = resp2.json()
                except:
                    data = {'status': 'unknown', 'message': resp2.text}
                
                ok = (
                    data.get('status') == 'success' 
                    or data.get('success') is True
                    or 'success' in str(data.get('message', '')).lower()
                )
                
                if ok:
                    logger.info(f"SMS reminder scheduled successfully (query params): {data}")
                    return {'success': True, 'response': data, 'message': data.get('message', 'Scheduled successfully')}
            
            error_msg = f'API returned {resp.status_code}: {resp.text[:500]}'
            logger.error(f"Failed to schedule SMS reminder: {error_msg}")
            return {'success': False, 'message': error_msg}
            
        except Exception as e:
            logger.error(f"Exception scheduling SMS reminder: {e}", exc_info=True)
            return {'success': False, 'message': str(e)}


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

def schedule_sms_reminder(phone_number: str, message: str, scheduled_at: str):
    return sms_service.schedule_sms_reminder(phone_number, message, scheduled_at)
