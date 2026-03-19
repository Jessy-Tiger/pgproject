# WhatsApp Notification System - Quick Reference

## One-Minute Setup

```bash
# 1. Install
pip install twilio

# 2. Configure .env
TWILIO_ACCOUNT_SID=AC1234567890...
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# 3. Test
python manage.py shell
>>> from vrllog.utils import send_whatsapp_message
>>> send_whatsapp_message('+919876543210', 'Hello from VRL!')
```

---

## Core Functions

### 1. Send WhatsApp Message
```python
from vrllog.utils import send_whatsapp_message

# Basic usage
message_sid = send_whatsapp_message(
    phone_number='+919876543210',
    message='Your pickup is confirmed!',
    message_type='notification'
)

# Returns:
# - message_sid (string) if successful
# - None if failed
```

### 2. Format Message
```python
from vrllog.utils import format_whatsapp_message

message = format_whatsapp_message('new_request', {
    'tracking_number': 'TRK123456',
    'sender_name': 'John Doe',
    'receiver_name': 'Jane Smith',
    'sender_address': 'Mumbai, India'
})
# Returns formatted message with emojis
```

### 3. Send Notification (Integrated)
```python
from vrllog.utils import send_whatsapp_notification
from vrllog.models import PickupRequest

pickup = PickupRequest.objects.get(id=1)
success = send_whatsapp_notification(
    pickup_request=pickup,
    notification_type='new_request',
    recipient_role='admin'
)

# Notification types:
# - new_request (to admin)
# - request_accepted (to customer)
# - request_rejected (to customer)
# - driver_assigned (to driver)
# - assignment_accepted (to driver)
# - assignment_reassigned (to customer)
# - assignment_waiting (to customer)
```

---

## Usage in Views

### Example 1: After Creating Pickup Request
```python
# In views.py
@require_http_methods(['POST'])
@login_required
def create_pickup(request):
    # ... create pickup request ...
    
    # Send notification
    send_whatsapp_notification(
        pickup_request=pickup_request,
        notification_type='new_request',
        recipient_role='admin'
    )
    
    return redirect('customer_dashboard')
```

### Example 2: Admin Accepts Request
```python
# In views.py
@require_http_methods(['POST'])
@login_required
def admin_accept_request(request, pickup_id):
    pickup_request = PickupRequest.objects.get(id=pickup_id)
    
    # Update status
    pickup_request.status = 'accepted'
    pickup_request.save()
    
    # Notify customer
    send_whatsapp_notification(
        pickup_request=pickup_request,
        notification_type='request_accepted',
        recipient_role='customer'
    )
    
    # Assign driver
    driver = get_available_driver()
    pickup_request.assigned_driver = driver
    pickup_request.save()
    
    # Notify driver
    send_whatsapp_notification(
        pickup_request=pickup_request,
        notification_type='driver_assigned',
        recipient_role='driver'
    )
    
    return redirect('admin_dashboard')
```

### Example 3: Handle Errors
```python
try:
    success = send_whatsapp_notification(
        pickup_request=pickup,
        notification_type='driver_assigned',
        recipient_role='driver'
    )
    
    if not success:
        messages.warning(request, 
            'Request processed, but notification failed')
except Exception as e:
    logger.error(f"WhatsApp error: {str(e)}")
    messages.warning(request, 
        'Request processed, notification system unavailable')
```

---

## Phone Number Handling

### Valid Formats
```python
# ✅ Correct (E.164 format)
'+919876543210'  # India
'+14155238886'   # USA
'+441632960018'  # UK

# ❌ Wrong
'9876543210'           # Missing country code
'919876543210'         # Missing + sign
'+91 9876543210'       # Spaces not allowed
'+91-9876543210'       # Hyphens not allowed
```

### Automatic Normalization
```python
# System automatically adds whatsapp: prefix
'+919876543210' → 'whatsapp:+919876543210'

# Validate before sending
phone = pickup_request.customer.profile.phone_number
if not phone.startswith('+'):
    phone = '+91' + phone  # Add country code
```

---

## Message Templates

### Template: new_request
```
🚚 *VRL Logistics*

New Pickup Request Created

📍 Tracking Number: TRK123456
👤 Sender: John Doe
📦 Receiver: Jane Smith
📮 Pickup From: Mumbai, Maharashtra

Our logistics team will process your request soon. 
You'll receive an update shortly!
```

### Template: request_accepted
```
✅ *VRL Logistics - Request Accepted*

Good News! Your pickup request has been accepted.

📍 Tracking Number: TRK123456
📅 Pickup Date/Time: 25-01-2024 at 10:00 AM
📮 Pickup Address: Mumbai, Maharashtra

A driver will be assigned shortly. Stay tuned!
```

### Template: driver_assigned
```
👨‍💼 *VRL Logistics - Driver Assigned*

A driver has been assigned to your request!

📍 Tracking Number: TRK123456
🚗 Driver: Rajesh Kumar
📱 Driver Contact: +919876543210
📅 Pickup Time: 10:00 AM

Confirm your presence at the pickup location.
```

---

## Configuration

### Settings to Know
```python
# In settings.py or .env

TWILIO_ACCOUNT_SID = 'AC1234567890...'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
WHATSAPP_NOTIFICATIONS_ENABLED = True
WHATSAPP_RETRY_ATTEMPTS = 3
WHATSAPP_RETRY_DELAY = 5
ADMIN_PHONE_NUMBER = '+919999999999'
```

### Disable Notifications (for testing)
```python
# In .env:
WHATSAPP_NOTIFICATIONS_ENABLED=False

# Messages will be logged but not sent
```

---

## Logging

### View Logs
```bash
# Real-time monitoring
tail -f vrllogistics/logs/whatsapp.log

# Count successful messages
grep "sent successfully" vrllogistics/logs/whatsapp.log | wc -l

# Count failed messages
grep "Failed to send" vrllogistics/logs/whatsapp.log | wc -l

# View specific error
grep "customer_phone" vrllogistics/logs/whatsapp.log
```

### Log Format
```
[2024-01-25 10:30:45,123] INFO: WhatsApp message sent successfully: SM123456789abc to whatsapp:+919876543210 (type: driver_assigned)
[2024-01-25 10:31:12,456] ERROR: Failed to send WhatsApp message to whatsapp:+919999999999: ValueError: Invalid phone number format
```

---

## Testing Checklist

### Unit Test
```python
from django.test import TestCase
from vrllog.utils import format_whatsapp_message

class WhatsAppTestCase(TestCase):
    def test_message_format(self):
        msg = format_whatsapp_message('new_request', {
            'tracking_number': 'TEST123',
            'sender_name': 'Test User',
            'receiver_name': 'Test Receiver',
            'sender_address': 'Test Address'
        })
        self.assertIn('TEST123', msg)
        self.assertIn('Test User', msg)
```

### Integration Test
```bash
# Create test pickup in shell
cd vrllogistics
python manage.py shell

from vrllog.models import PickupRequest, User
from vrllog.utils import send_whatsapp_notification

# Get test pickup
pickup = PickupRequest.objects.first()

# Send test notification
result = send_whatsapp_notification(
    pickup_request=pickup,
    notification_type='new_request',
    recipient_role='admin'
)
print(f"Success: {result}")

# Check logs
exit()
tail -f logs/whatsapp.log
```

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| "Twilio library not found" | `pip install twilio` |
| "Invalid credentials" | Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env |
| "Phone not in sandbox" | Send "join CODE" to sandbox number on WhatsApp |
| "Message rate limit" | Increase WHATSAPP_RETRY_DELAY to 10+ |
| "No logs directory" | `mkdir vrllogistics/logs` |
| "Phone number validation errors" | Use format: +91XXXXXXXXXX (E.164) |

---

## Environment Variables

**.env file template:**
```bash
# Twilio Credentials (Get from console.twilio.com)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=yyyyyyyyyyyyyyyyyy
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Feature Flags
WHATSAPP_NOTIFICATIONS_ENABLED=True

# Retry Configuration
WHATSAPP_RETRY_ATTEMPTS=3
WHATSAPP_RETRY_DELAY=5

# Admin Contact
ADMIN_PHONE_NUMBER=+919876543210
```

**Never commit .env to Git!**

---

## Performance Tips

### 1. Async Sending (Future Enhancement)
```python
# Using Celery (not required for MVP)
from celery import shared_task

@shared_task
def send_whatsapp_async(phone_number, message):
    return send_whatsapp_message(phone_number, message)

# Call in view
send_whatsapp_async.delay('+919876543210', 'Hello!')
```

### 2. Batch Messages
```python
# Don't send 100 messages in a loop
# Instead, queue them with delays

import time
for phone in phones:
    send_whatsapp_message(phone, message)
    time.sleep(0.5)  # Rate limit
```

### 3. Optimize Logging
```python
# Don't log sensitive data
logger.error(f"Failed to send to {phone}")  # ❌
logger.error(f"Failed to send to user {user_id}")  # ✅
```

---

## Deployment Checklist

- [ ] Install Twilio SDK: `pip install twilio`
- [ ] Copy .env.example to .env
- [ ] Fill in Twilio credentials
- [ ] Run `python manage.py check`
- [ ] Test with real Twilio account
- [ ] Create logs directory: `mkdir vrllogistics/logs`
- [ ] Set proper permissions: `chmod 755 vrllogistics/logs`
- [ ] Test notification in Django shell
- [ ] Monitor whatsapp.log
- [ ] Deploy to production

---

## API Reference

### send_whatsapp_message()
```python
def send_whatsapp_message(phone_number, message, message_type='notification')
    """
    Args:
        phone_number: str in format +91XXXXXXXXXX
        message: str (max 1600 chars)
        message_type: str (notification, alert, confirmation)
    
    Returns:
        str: message_sid if successful
        None: if failed
    """
```

### send_whatsapp_notification()
```python
def send_whatsapp_notification(pickup_request, notification_type, 
                               recipient_role, reason=None)
    """
    Args:
        pickup_request: PickupRequest object
        notification_type: str (new_request, request_accepted, etc.)
        recipient_role: str ('customer', 'admin', 'driver')
        reason: str (optional, for rejections)
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
```

### format_whatsapp_message()
```python
def format_whatsapp_message(template_name, context=None)
    """
    Args:
        template_name: str (new_request, request_accepted, etc.)
        context: dict with template variables
    
    Returns:
        str: Formatted message text
    """
```

---

## Resources

- **Twilio Console:** https://console.twilio.com
- **Twilio Docs:** https://www.twilio.com/docs/whatsapp
- **Python SDK:** https://twilio-python.readthedocs.io
- **Setup Guide:** [WHATSAPP_SETUP.md](./WHATSAPP_SETUP.md)
- **Migration Summary:** [MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md)

---

## Support

**For detailed instructions, see:**
- Setup & Installation: [WHATSAPP_SETUP.md](./WHATSAPP_SETUP.md)
- Configuration Guide: [WHATSAPP_SETUP.md#configuration](./WHATSAPP_SETUP.md)
- Troubleshooting: [WHATSAPP_SETUP.md#troubleshooting](./WHATSAPP_SETUP.md)

**Version:** 2.0 (WhatsApp System)  
**Last Updated:** 2024
