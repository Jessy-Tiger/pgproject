# Email Notification System Documentation

## Overview

The VRL Logistics project includes a comprehensive email notification system that sends notifications to customers, drivers, and admins at key points in the pickup lifecycle. This document explains how the system works, how to configure it, and how to extend it.

## System Architecture

### Components

1. **Email Configuration (`settings.py`)**
   - Gmail SMTP configuration with environment variables
   - Logging setup for email debugging
   - Fallback to console email backend in development

2. **Email Utility Function (`utils.py`)**
   - `send_email_notification()` - Main dispatcher function
   - `_get_email_config()` - Configuration mapper
   - `_send_email()` - Standard email sender
   - `_send_email_with_attachment()` - Email with PDF attachments
   - `handle_email_errors` - Decorator for error handling

3. **Email Templates (`templates/emails/`)**
   - HTML templates for each notification type
   - Consistent styling and branding
   - Dynamic content via Django template variables

4. **Email Triggers (`views.py`)**
   - Views call `send_email_notification()` at appropriate points
   - Defensive error handling prevents email failures from breaking workflows
   - Logging provides audit trail of all email attempts

## Email Notification Types

### 1. New Request (Admin)

**When:** Customer creates a new pickup request
**Recipient:** Admin
**Template:** `emails/new_request_admin.html`
**Usage:**
```python
send_email_notification(
    pickup_request=pickup_request,
    notification_type='new_request',
    recipient_role='admin'
)
```

**Context Variables:**
- `pickup_request` - The PickupRequest object

### 2. Request Accepted (Customer)

**When:** Admin accepts the pickup request
**Recipient:** Customer
**Template:** `emails/request_accepted_customer.html`
**Attachments:** Invoice PDF (if invoice exists)
**Usage:**
```python
send_email_notification(
    pickup_request=pickup_request,
    notification_type='request_accepted',
    recipient_role='customer',
    invoice=invoice  # Optional
)
```

**Context Variables:**
- `pickup_request` - The PickupRequest object
- `customer_name` - Customer's first name

### 3. Request Rejected (Customer)

**When:** Admin rejects the pickup request
**Recipient:** Customer
**Template:** `emails/request_rejected_customer.html`
**Usage:**
```python
send_email_notification(
    pickup_request=pickup_request,
    notification_type='request_rejected',
    recipient_role='customer',
    reason='Unable to deliver to this area'
)
```

**Context Variables:**
- `pickup_request` - The PickupRequest object
- `customer_name` - Customer's first name
- `rejection_reason` - Reason for rejection

### 4. Driver Assigned (Driver)

**When:** Driver is assigned to a pickup request
**Recipient:** Driver
**Template:** `emails/driver_assigned.html`
**Usage:**
```python
send_email_notification(
    pickup_request=pickup_request,
    notification_type='driver_assigned',
    recipient_role='driver'
)
```

**Context Variables:**
- `pickup_request` - The PickupRequest object
- `driver_name` - Driver's first name

### 5. Status Update (Customer)

**When:** Pickup status changes during transit
**Recipient:** Customer
**Template:** `emails/status_update_customer.html`
**Usage:**
```python
send_email_notification(
    pickup_request=pickup_request,
    notification_type='status_update',
    recipient_role='customer'
)
```

**Context Variables:**
- `pickup_request` - The PickupRequest object
- `customer_name` - Customer's first name
- `new_status` - Human-readable status label

### 6. Assignment Accepted (Driver)

**When:** Driver accepts the assignment
**Recipient:** Driver
**Template:** `emails/assignment_accepted_driver.html`
**Usage:**
```python
send_email_notification(
    pickup_request=pickup_request,
    notification_type='assignment_accepted',
    recipient_role='driver'
)
```

**Context Variables:**
- `pickup_request` - The PickupRequest object
- `driver_name` - Driver's first name

### 7. Assignment Reassigned (Customer)

**When:** Assigned driver rejects, request reassigned to another driver
**Recipient:** Customer
**Template:** `emails/assignment_reassigned_customer.html`
**Usage:**
```python
send_email_notification(
    pickup_request=pickup_request,
    notification_type='assignment_reassigned',
    recipient_role='customer',
    reason='Previous driver unavailable'
)
```

**Context Variables:**
- `pickup_request` - The PickupRequest object
- `customer_name` - Customer's first name
- `reason` - Reason for reassignment

### 8. Assignment Waiting (Customer)

**When:** No drivers available after assignment rejection
**Recipient:** Customer
**Template:** `emails/assignment_waiting_customer.html`
**Usage:**
```python
send_email_notification(
    pickup_request=pickup_request,
    notification_type='assignment_waiting',
    recipient_role='customer',
    reason='High demand, finding driver'
)
```

**Context Variables:**
- `pickup_request` - The PickupRequest object
- `customer_name` - Customer's first name
- `reason` - Why waiting (driver availability, etc.)

## Configuration

### Step 1: Gmail Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an app-specific password:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device type
   - Google will generate a 16-character password
3. Copy the password (includes spaces - don't remove them)

### Step 2: Environment Variables

1. Navigate to the vrllogistics directory
2. Copy the template file:
   ```
   cp .env.example .env
   ```
3. Edit `.env` and fill in your Gmail credentials:
   ```
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```
4. Add `.env` to `.gitignore`:
   ```
   echo ".env" >> .gitignore
   ```

### Step 3: Install python-decouple (Optional but Recommended)

For better environment variable handling:
```bash
pip install python-decouple
```

Then update `settings.py`:
```python
from decouple import config

EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
```

### Step 4: Test Email Configuration

Run Django shell:
```bash
python manage.py shell
```

Then test:
```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email',
    'If you see this, email is working!',
    settings.DEFAULT_FROM_EMAIL,
    ['test@example.com'],
    fail_silently=False,
)
```

## Logging & Debugging

### Log Files

Email logs are stored in `vrllogistics/logs/`:

- **email.log** - All email notification activities
- **django.log** - Django framework warnings
- **error.log** - All application errors

### View Logs

```bash
# Real-time email log
tail -f vrllogistics/logs/email.log

# Search for errors
grep "ERROR" vrllogistics/logs/email.log

# Search for specific email type
grep "assignment_accepted" vrllogistics/logs/email.log

# Count email attempts
wc -l vrllogistics/logs/email.log
```

### Log Format

```
ERROR 2024-01-15 18:45:30 utils 12345 67890 Email template not found: emails/test.html
```

Fields:
- **ERROR** - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **2024-01-15 18:45:30** - Timestamp
- **utils** - Module/logger name
- **12345** - Process ID
- **67890** - Thread ID
- **Message** - The error or info message

### Development Mode

To test emails without sending them, set in `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Emails will be printed to console instead of being sent.

## Error Handling

### Defensive Programming

The email system uses try-catch blocks in views to prevent email failures from breaking the user workflow:

```python
try:
    send_email_notification(
        pickup_request=pickup_request,
        notification_type='driver_assigned',
        recipient_role='driver'
    )
except Exception as e:
    logger.error(f"Failed to send email: {str(e)}")
    # User workflow continues despite email failure
```

### Return Values

`send_email_notification()` returns:
- `True` - Email sent successfully
- `False` - Email failed (check logs for details)

Example usage:
```python
if not send_email_notification(...):
    logger.warning("Email notification failed for pickup...")
```

## Adding New Notification Types

To add a new notification type:

### 1. Create Template File

Create `templates/emails/new_notification_type.html` with your HTML content:

```html
<html>
<head>
    <style>
        /* Your CSS here */
    </style>
</head>
<body>
    <div class="container">
        <!-- Your template content using {{ context_variables }} -->
    </div>
</body>
</html>
```

### 2. Add Configuration in utils.py

In `_get_email_config()` function, add a new condition:

```python
elif notification_type == 'new_type' and recipient_role == 'customer':
    config = {
        'subject': f'Subject Line - {pickup_request.tracking_number}',
        'recipient_email': pickup_request.customer.email,
        'template_name': 'emails/new_notification_type.html',
        'context': {
            'pickup_request': pickup_request,
            'customer_name': pickup_request.customer.first_name or pickup_request.customer.username,
            # Add other context variables
        },
        'headers': {}
    }
```

### 3. Call from View

```python
send_email_notification(
    pickup_request=pickup_request,
    notification_type='new_type',
    recipient_role='customer'
)
```

### 4. Check Logs

Monitor `vrllogistics/logs/email.log` to verify email was sent:

```bash
grep "new_type" vrllogistics/logs/email.log
```

## Production Checklist

Before deploying to production:

- [ ] Set `DEBUG = False` in settings.py
- [ ] Move all sensitive data (passwords, API keys) to environment variables
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Enable HTTPS/SSL:
  - [ ] Set `SECURE_SSL_REDIRECT = True`
  - [ ] Set `SESSION_COOKIE_SECURE = True`
  - [ ] Set `CSRF_COOKIE_SECURE = True`
- [ ] Test email sending with real Gmail account
- [ ] Monitor `vrllogistics/logs/email.log` for errors
- [ ] Set up log rotation to prevent logs from growing too large
- [ ] Test all notification types with real data
- [ ] Verify reply-to headers for customer emails:
  ```python
  'headers': {'Reply-To': 'noreply@vrllogistics.com'}
  ```

## Troubleshooting Guide

### Problem: "SMTPAuthenticationError: Username and Password not accepted"

**Solution:**
1. Verify you're using app-specific password, not regular Gmail password
2. Generator app password at: https://myaccount.google.com/apppasswords
3. Ensure 2-Factor Authentication is enabled
4. Check EMAIL_HOST_USER matches your Gmail account exactly
5. Verify EMAIL_HOST_PASSWORD has correct 16 characters (spaces are normal)

### Problem: "Connection refused" or "timeout"

**Solution:**
1. Verify EMAIL_HOST = 'smtp.gmail.com'
2. Verify EMAIL_PORT = 587
3. Verify EMAIL_USE_TLS = True
4. Check firewall allows outgoing SMTP (port 587)
5. Test with console backend first:
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
   ```

### Problem: "Template does not exist: emails/xxx.html"

**Solution:**
1. Verify template file exists in `templates/emails/` directory
2. Check exact filename (case-sensitive)
3. Verify TEMPLATES configuration in settings.py includes correct directory
4. Run: `python manage.py check`

### Problem: Email sent but recipient doesn't receive

**Solution:**
1. Check Gmail's Sent folder - verify email was actually sent
2. Check recipient's spam/junk folder
3. Verify recipient email address is correct in database:
   ```python
   python manage.py shell
   >>> from vrllog.models import PickupRequest
   >>> p = PickupRequest.objects.first()
   >>> p.customer.email
   ```
4. Check logs for any errors:
   ```bash
   grep "ERROR" vrllogistics/logs/email.log
   ```

### Problem: Emails not sending but no errors

**Solution:**
1. Check EMAIL_BACKEND - make sure it's not set to console backend:
   ```python
   print(settings.EMAIL_BACKEND)  # In Django shell
   ```
2. Verify EMAIL_HOST_PASSWORD is correct (regenerate if needed)
3. Check logs:
   ```bash
   tail -f vrllogistics/logs/email.log
   ```
4. Test manually in Django shell:
   ```python
   from django.core.mail import send_mail
   from django.conf import settings
   send_mail('Test', 'Test message', settings.DEFAULT_FROM_EMAIL, ['test@example.com'])
   ```

## Performance Considerations

### Email Sending Speed

- Typical email send time: 1-3 seconds per email
- Network latency: 500ms - 2 seconds
- Template rendering: 100-500ms

### Optimization Tips

1. **Batch sending:** For bulk emails (e.g., daily digest):
   ```python
   from django.core.mail import send_mass_mail
   message_list = [
       ('Subject 1', 'Message 1', 'from@example.com', ['to1@example.com']),
       ('Subject 2', 'Message 2', 'from@example.com', ['to2@example.com']),
   ]
   send_mass_mail(message_list, fail_silently=False)
   ```

2. **Async sending:** For non-blocking email (requires Celery):
   ```python
   from celery import shared_task
   
   @shared_task
   def send_notification_async(pickup_id, notification_type):
       pickup = PickupRequest.objects.get(id=pickup_id)
       send_email_notification(pickup, notification_type, 'customer')
   ```

3. **Queue management:** For high-volume emails, consider:
   - Rq-scheduler
   - Celery with Redis
   - AWS SES (Simple Email Service)

## References

- [Django Email Documentation](https://docs.djangoproject.com/en/6.0/topics/email/)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [Email Best Practices](https://www.smashingmagazine.com/2017/09/guide-build-emails/)
- [SMTP Port 587 vs 465](https://www.mailgun.com/blog/email-validation/smtp-ports/)

## Support

For issues or questions:

1. Check the Troubleshooting Guide above
2. Review logs in `vrllogistics/logs/email.log`
3. Test with Django shell
4. Enable DEBUG mode to see detailed error messages
5. Check Django system checks: `python manage.py check`