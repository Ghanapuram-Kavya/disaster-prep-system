import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN  = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE       = os.getenv('TWILIO_PHONE', '')

def clean_phone(phone):
    """Convert to international format +91XXXXXXXXXX"""
    phone = str(phone).strip()
    phone = phone.replace(' ', '').replace('-', '')
    if phone.startswith('+'):
        return phone
    phone = phone.replace('+91', '').lstrip('0')
    if len(phone) == 10:
        return '+91' + phone
    return phone


def send_sms(to_number, message):
    """Send SMS via Twilio"""
    try:
        from twilio.rest import Client

        phone = clean_phone(to_number)
        print(f"Sending SMS to: {phone}")

        client = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = client.messages.create(
            body  = message[:160],
            from_ = TWILIO_NUMBER,
            to    = phone
        )
        print(f"SMS sent! SID: {msg.sid}")
        return {'success': True, 'sid': msg.sid}

    except Exception as e:
        print(f"SMS error for {to_number}: {e}")
        return {'success': False, 'error': str(e)}


def send_bulk_sms(phone_list, message):
    """Send SMS to multiple numbers"""
    sent   = 0
    failed = 0
    for phone in phone_list:
        result = send_sms(phone, message)
        if result['success']:
            sent += 1
        else:
            failed += 1
    print(f"Bulk SMS: {sent} sent, {failed} failed")
    return {'sent': sent, 'failed': failed}