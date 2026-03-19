# VRL Logistics - WhatsApp Notification System Setup Guide

## Overview

The VRL Logistics application has been upgraded from an email-based notification system to a **WhatsApp-based notification system** powered by **Twilio API**. This guide provides step-by-step instructions for setting up and deploying the WhatsApp notification system.

## Table of Contents

1. [Why WhatsApp?](#why-whatsapp)
2. [Prerequisites](#prerequisites)
3. [System Architecture](#system-architecture)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [Notification Types](#notification-types)
7. [Testing WhatsApp Messages](#testing-whatsapp-messages)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)
10. [Message Formatting](#message-formatting)
11. [Rate Limiting & Best Practices](#rate-limiting--best-practices)

---

## Why WhatsApp?

**Advantages over Email:**
- **Instant Delivery**: Messages delivered in seconds, not minutes/hours
- **Higher Read Rates**: WhatsApp messages have 95%+ open rates vs 20-30% for emails
- **Better Engagement**: Real-time updates keep customers informed
- **International Reach**: Works globally without SMS carrier limitations
- **Cost-Effective**: Twilio WhatsApp pricing is competitive and predictable
- **Mobile-First**: 99% of WhatsApp users access via mobile (your target users)

---

## Prerequisites

### Required Software
- Python 3.8+
- Django 6.0+
- pip (Python package manager)
- Twilio account (free tier available)

### Required Accounts
- **Twilio Account** (https://www.twilio.com/console)
- **Twilio WhatsApp Sandbox** (free for testing) or WhatsApp Business Account (production)

### System Requirements
- Internet connection (for Twilio API calls)
- 2MB+ free disk space for logging
- Mobile phone with WhatsApp installed (for testing)

---

## System Architecture

### Component Diagram

```
┌─────────────────────┐
│   Django Views      │
│   (views.py)        │
└──────────┬──────────┘
           │ calls
           ▼
┌─────────────────────────────────┐
│  WhatsApp Dispatcher            │
│  (send_whatsapp_notification)   │
└──────────┬──────────────────────┘
           │ validates & formats
           ▼
┌─────────────────────────────────┐
│  Message Formatter              │
│  (format_whatsapp_message)      │
└──────────┬──────────────────────┘
           │ converts to text
           ▼
┌─────────────────────────────────┐
│  WhatsApp Sender                │
│  (send_whatsapp_message)        │
└──────────┬──────────────────────┘
           │ with retry logic
           ▼
┌─────────────────────────────────┐
│  Twilio API Client              │
│  (twilio.rest.Client)           │
└──────────┬──────────────────────┘
           │ HTTP/REST API
           ▼
        Twilio
           │
           ▼
      WhatsApp
           │
           ▼
    User's Phone 📱
```

### Data Flow

1. **Action** → Pickup request created, driver assigned, etc.
2. **Dispatcher** → `send_whatsapp_notification()` called with request details
3. **Config** → `_get_whatsapp_config()` retrieves phone number & template
4. **Format** → `format_whatsapp_message()` creates formatted message text
5. **Send** → `send_whatsapp_message()` sends via Twilio with retries
6. **Log** → Success/failure recorded in `whatsapp.log`
7. **Retry** → Failed messages retried up to 3 times (configurable)

---

## Installation & Setup

### Step 1: Install Twilio Python SDK

```bash
# Activate your virtual environment (if using venv)
source ms/Scripts/activate  # On Windows, use: ms\Scripts\activate.bat

# Install Twilio package
pip install twilio

# Verify installation
python -c "from twilio.rest import Client; print('Twilio installed successfully!')"
```

### Step 2: Create Twilio Account

1. **Sign up** at https://www.twilio.com/console
2. **Verify your email** and phone number
3. Get your **Account SID** and **Auth Token** from the dashboard
4. Note these credentials (you'll need them for .env)

### Step 3: Enable WhatsApp Sandbox (Testing)

1. Go to **Consol → Messaging → Services**
2. Create a new Messaging Service
3. Select **WhatsApp** channel
4. Join the **Twilio WhatsApp Sandbox** (get sandbox number like `whatsapp:+14155238886`)
5. Add your phone number to sandbox: Send "join YOUR_CODE" to sandbox number
6. Confirm WhatsApp on your phone

### Step 4: Configure .env File

Create `.env` file in project root:

```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Add Twilio credentials:

```env
TWILIO_ACCOUNT_SID=AC1234567890abcdefghijklmnopqrstu
TWILIO_AUTH_TOKEN=your_auth_token_here_keep_secret
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
WHATSAPP_NOTIFICATIONS_ENABLED=True
WHATSAPP_RETRY_ATTEMPTS=3
WHATSAPP_RETRY_DELAY=5
ADMIN_PHONE_NUMBER=+919876543210
```

**⚠️ SECURITY WARNING:** 
- Never commit `.env` to Git
- Add `.env` to `.gitignore`
- Rotate tokens regularly
- Use [Twilio Secret Management](https://www.twilio.com/docs/glossary/what-are-environment-variables)

### Step 5: Update Django Settings

✅ **Already Done** - No manual action needed, but verify:

In `vrllogistics/settings.py`:

```python
# Verify these are set
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
WHATSAPP_NOTIFICATIONS_ENABLED = os.getenv('WHATSAPP_NOTIFICATIONS_ENABLED', 'True').lower() == 'true'
WHATSAPP_RETRY_ATTEMPTS = int(os.getenv('WHATSAPP_RETRY_ATTEMPTS', 3))
WHATSAPP_RETRY_DELAY = int(os.getenv('WHATSAPP_RETRY_DELAY', 5))
```

### Step 6: Verify Installation

```bash
# Run Django system check
cd vrllogistics
python manage.py check

# Expected output: System check identified no issues (0 silenced).
```

---

## Configuration

### Phone Number Formats

WhatsApp messages require phone numbers in **E.164 international format**:

**Valid Formats:**
- `+919876543210` (India)
- `+14155238886` (USA)
- `+441632960018` (UK)

**Invalid Formats (will fail):**
- `9876543210` (missing country code)
- `919876543210` (missing + sign)
- `+91 9876543210` (spaces not allowed)
- `+91-9876543210` (hyphens not allowed)

### Automatic Phone Number Normalization

The system automatically normalizes phone numbers by:

1. Adding `whatsapp:` prefix if missing
2. Validating international format
3. Logging invalid numbers

### Disabling WhatsApp in Development

To test without sending real WhatsApp messages:

```python
# In settings.py or .env
WHATSAPP_NOTIFICATIONS_ENABLED=False

# Messages will be logged but not sent
```

---

## Notification Types

The system supports **8 notification types** for different events:

### 1. **new_request** (Admin)
**Event:** Customer creates pickup request
**Recipient:** Admin
**Message:** Displays tracking number, sender, receiver, pickup address

### 2. **request_accepted** (Customer)
**Event:** Admin accepts the pickup request
**Recipient:** Customer
**Message:** Confirmation with pickup date, time, and address

### 3. **request_rejected** (Customer)
**Event:** Admin rejects the request
**Recipient:** Customer
**Message:** Rejection notice with reason provided by admin

### 4. **driver_assigned** (Driver)
**Event:** Driver is assigned to pickup
**Recipient:** Driver
**Message:** Assignment details, customer name, pickup time

### 5. **assignment_accepted** (Driver)
**Event:** Driver accepts the assignment
**Recipient:** Driver
**Message:** Confirmation of accepted assignment with details

### 6. **assignment_reassigned** (Customer)
**Event:** Driver rejects and another is assigned
**Recipient:** Customer
**Message:** Update about new driver assignment

### 7. **assignment_waiting** (Customer)
**Event:** No drivers available, waiting for one
**Recipient:** Customer
**Message:** Waiting notification, system will retry

### 8. **status_update** (Customer)
**Event:** Pickup status changes (picked up, in transit, delivered)
**Recipient:** Customer
**Message:** Status update with current location and ETA

---

## Testing WhatsApp Messages

### Manual Testing

Use Django shell to test:

```bash
cd vrllogistics
python manage.py shell

# Import required modules
from vrllog.models import PickupRequest
from vrllog.utils import send_whatsapp_message, format_whatsapp_message

# Test 1: Send simple message
result = send_whatsapp_message(
    phone_number='+91YOUR_PHONE_NUMBER',
    message='Test message from VRL Logistics',
    message_type='test'
)
print(f"Message SID: {result}")  # Will print message ID if successful

# Test 2: Format and send notification
pickup = PickupRequest.objects.first()
message = format_whatsapp_message('new_request', {
    'tracking_number': pickup.tracking_number,
    'sender_name': pickup.sender_name,
    'receiver_name': pickup.receiver_name,
    'sender_address': f"{pickup.sender_address}, {pickup.sender_city}"
})
print(f"Formatted message:\n{message}")

# Exit shell
exit()
```

### Automated Testing

Run Django tests:

```bash
python manage.py test vrllog.tests
```

### Check Logs

Monitor WhatsApp activity:

```bash
# View WhatsApp log
tail -f vrllogistics/logs/whatsapp.log

# View all logs
tail -f vrllogistics/logs/*.log
```

### Common Test Scenarios

**Scenario 1: New customer creates request**
```
✅ Customer receives "new_request" notification
✅ Admin receives alert
⏱️ Message arrives in 1-3 seconds
```

**Scenario 2: Admin accepts request**
```
✅ Customer gets "request_accepted" notification
✅ Driver gets "driver_assigned" notification
⏱️ Both receive messages simultaneously
```

**Scenario 3: Driver accepts assignment**
```
✅ Customer gets "assignment_accepted" notification
⏱️ Real-time confirmation
```

---

## Troubleshooting

### Issue: "Twilio library not installed"

**Solution:**
```bash
pip install twilio
python -c "from twilio.rest import Client; print('OK')"
```

### Issue: "Invalid Account SID or Token"

**Diagnosis:**
```bash
# Verify credentials in .env
cat .env | grep TWILIO

# Check Twilio console for correct values:
# https://www.twilio.com/console
```

**Solution:**
- Copy exact Account SID from Twilio Console (no whitespace)
- Generate new Auth Token if needed
- Restart Django: `python manage.py runserver`

### Issue: "Phone number not in WhatsApp sandbox"

**Solution:**
1. Send "join YOUR_SANDBOX_CODE" to Twilio sandbox number
2. Confirm WhatsApp message
3. Wait 30 seconds
4. Try sending message again

### Issue: "Message rate limit exceeded"

**Cause:** Sending too many messages too quickly
**Solution:**
- Increase `WHATSAPP_RETRY_DELAY` to 10+ seconds
- Implement queue system for bulk messages (future enhancement)

### Issue: "Messages not arriving"

**Checklist:**
```
☑ WhatsApp app is installed and active
☑ Phone number is in correct format (+91XXXXXXXXXX)
☑ Twilio account is active (not paused/suspended)
☑ WHATSAPP_NOTIFICATIONS_ENABLED=True in .env
☑ Internet connection is working
☑ Check whatsapp.log for errors
```

### Issue: "Database errors with phone numbers"

**Solution:**
Ensure `UserProfile.phone_number` field exists:

```python
# In models.py
phone_number = models.CharField(max_length=20, blank=True)

# Run migration if needed
python manage.py migrate
```

### Enable Debug Logging

```python
# In settings.py
LOGGING = {
    'loggers': {
        'vrllog.utils': {
            'level': 'DEBUG',  # Changed from INFO
        }
    }
}

# Then restart and check logs
tail -f vrllogistics/logs/whatsapp.log
```

---

## Production Deployment

### Step 1: Upgrade Twilio Account

1. Move from Sandbox to **WhatsApp Business Account**
2. Apply for official business number
3. Get WhatsApp Business API approval (~1-2 days)
4. Update `TWILIO_WHATSAPP_NUMBER` in production `.env`

### Step 2: Phone Number Management

**Update Customer Phone Numbers:**
```python
# In views.py or management command
from vrllog.models import UserProfile

profiles = UserProfile.objects.filter(phone_number='')
# Collect phone numbers from signup forms

# Ensure format standardization
def normalize_phone(phone):
    phone = phone.replace(' ', '').replace('-', '')
    if not phone.startswith('+'):
        phone = '+91' + phone  # Add country code if missing
    return phone
```

### Step 3: Message Templates (Optional)

Twilio supports **message templates** for:
- Improved delivery rates
- Compliance with WhatsApp policies
- Partner-level business messaging

Set up templates:
1. Create template in WhatsApp Manager
2. Use template name in `format_whatsapp_message()`
3. Reduces character count and improves deliverability

### Step 4: Monitoring in Production

**Set up alerts for:**
```
- Failed message deliveries (check logs hourly)
- Rate limit warnings
- Auth token expiration
- Account balance threshold
```

**Dashboard Setup:**
```bash
# Install monitoring (optional)
pip install django-monitoring

# Create custom dashboard in Django admin
# Track: messages_sent, messages_failed, delivery_rate
```

### Step 5: Load Testing

**Before going live, test with:**
- 100 concurrent customers
- 1000 messages/hour
- Verify retry mechanism under load
- Check database query performance

```python
# settings.py - production optimizations
WHATSAPP_RETRY_ATTEMPTS = 2  # Reduce retries in production
WHATSAPP_RETRY_DELAY = 3     # Faster retries
ATOMIC_REQUESTS = True       # Database transactions
```

### Step 6: Backup & Recovery

**Implement backup strategy:**
```bash
# Backup logs
tar -czf whatsapp_logs_backup_$(date +%Y%m%d).tar.gz vrllogistics/logs/

# Backup database before major changes
python manage.py dumpdata > data_backup_$(date +%Y%m%d).json
```

---

## Message Formatting

### Template Variables

Each template uses specific variables formatted dynamically:

**new_request template:**
```
{tracking_number}  - Unique tracking number
{sender_name}      - Sender's full name
{receiver_name}    - Receiver's full name
{sender_address}   - Pickup location
```

**request_accepted template:**
```
{tracking_number}  - Unique tracking number
{pickup_date}      - Date in DD-MM-YYYY format
{pickup_time}      - Time (HH:MM format)
{pickup_address}   - Full address
```

### Character Limits

WhatsApp messages have a **1600 character limit** per message.

**Current templates:** 200-400 characters (well within limit)

**Ensure when customizing:**
```
message = format_whatsapp_message('new_request', context)
if len(message) > 1600:
    logger.warning(f"Message too long: {len(message)} chars")
    # Truncate or split message
```

### Custom Templates

To add custom notification types:

```python
# In utils.py - format_whatsapp_message()
templates = {
    'your_new_type': (
        "🚚 *VRL Logistics - Your Message*\n\n"
        "Your custom message here\n"
        "{tracking_number}\n"
    )
}
```

---

## Rate Limiting & Best Practices

### Twilio Rate Limits

- **Default:** 10 messages/second
- **Enterprise:** Negotiable

For VRL Logistics scale (expected 500-1000 messages/day):
```
Messages/second: 1000/(24*60*60) = 0.01 msg/s ✅ Well within limits
```

### Best Practices

**1. Always validate phone numbers:**
```python
import re

def is_valid_whatsapp_number(phone):
    # E.164 format: +[country][number]
    pattern = r'^\+\d{1,3}\d{5,14}$'
    return re.match(pattern, phone) is not None
```

**2. Implement message queueing (future):**
```python
# Prevent message bursts
from celery import shared_task

@shared_task
def send_whatsapp_async(phone_number, message):
    return send_whatsapp_message(phone_number, message)
```

**3. Monitor delivery health:**
```python
# In logs/dashboard
- Messages sent: Count
- Messages failed: Count
- Average delivery time: Seconds
- Failure rate: Percentage
```

**4. Handle timeouts gracefully:**
```python
# In utils.py already implemented:
WHATSAPP_RETRY_ATTEMPTS = 3
WHATSAPP_RETRY_DELAY = 5  # seconds
```

**5. Log everything:**
```python
# All messages logged to whatsapp.log
# Includes: timestamp, phone, message type, status, error details
logger.info(f"WhatsApp message sent: {message_obj.sid}")
logger.error(f"Failed to send: {str(e)}")
```

### Cost Estimation

**Twilio WhatsApp Pricing** (as of 2024):
- **Outbound (from business):** $0.0075 per message (US pricing)
- **Inbound (from customer):** Free
- **Template-based:** May be discounted

**VRL Logistics Estimate:**
- 1000 messages/day = $7.50/day = $225/month
- Includes retry messages and errors
- Enterprise customers: Negotiate volume discounts

---

## Summary Checklist

✅ **Installation Complete**
- [ ] Python 3.8+ installed
- [ ] Twilio SDK installed: `pip install twilio`
- [ ] Twilio account created
- [ ] WhatsApp sandbox configured
- [ ] .env file created with credentials
- [ ] `python manage.py check` shows no errors

✅ **Configuration Complete**
- [ ] Settings.py has Twilio config
- [ ] Phone numbers in database
- [ ] WHATSAPP_NOTIFICATIONS_ENABLED=True
- [ ] Logging directory created (vrllogistics/logs/)

✅ **Testing Complete**
- [ ] Manual test message sent successfully
- [ ] Django views call send_whatsapp_notification
- [ ] whatsapp.log file is created
- [ ] Customer receives test message

✅ **Production Ready**
- [ ] Twilio account upgraded to WhatsApp Business
- [ ] Production phone numbers configured
- [ ] Load testing completed
- [ ] Monitoring dashboard set up
- [ ] Database backups automated
- [ ] Team trained on system

---

## Support & Further Reading

- **Twilio Docs:** https://www.twilio.com/docs/whatsapp
- **WhatsApp API Guide:** https://manuals.info.apple.com/MANUALS/1000/MA1902/en_US/
- **Django Email Documentation:** https://docs.djangoproject.com/en/6.0/topics/email/
- **Twilio Python SDK:** https://twilio-python.readthedocs.io/

## Next Steps

1. **Short-term (Next week):**
   - Deploy to staging environment
   - Test with real customer data
   - Monitor logs for errors

2. **Medium-term (Next month):**
   - Upgrade to WhatsApp Business Account
   - Deploy to production
   - Collect user feedback

3. **Long-term (Next quarter):**
   - Implement message analytics dashboard
   - Add message templating for better formatting
   - Integrate SMS fallback (if WhatsApp fails)
   - Build customer communication preferences

---

**Last Updated:** 2024
**Maintained By:** VRL Logistics Development Team
**Version:** 2.0 (WhatsApp System)
