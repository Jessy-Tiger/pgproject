# Email System - Code Examples & Quick Reference

## Quick Usage Examples

### 1. Send Email on Pickup Creation

```python
from vrllog.utils import send_email_notification

# In your view
def create_pickup(request):
    if form.is_valid():
        pickup_request = form.save(commit=False)
        pickup_request.customer = request.user
        pickup_request.save()
        
        # Send admin notification
        send_email_notification(
            pickup_request=pickup_request,
            notification_type='new_request',
            recipient_role='admin'
        )
        
        return redirect('pickup_detail', pk=pickup_request.id)
```

### 2. Send Email with Error Handling

```python
import logging

logger = logging.getLogger(__name__)

def accept_request(request, pickup_id):
    pickup = get_object_or_404(PickupRequest, id=pickup_id)
    
    # Update status
    pickup.status = 'accepted'
    pickup.save()
    
    # Send email with error handling
    try:
        success = send_email_notification(
            pickup_request=pickup,
            notification_type='request_accepted',
            recipient_role='customer'
        )
        if not success:
            logging.warning(f"Email failed for pickup {pickup_id}")
    except Exception as e:
        logger.error(f"Exception sending email: {str(e)}")
    
    return redirect('dashboard')
```

### 3. Send Email with Invoice Attachment

```python
from vrllog.models import Invoice

# After creating invoice
invoice = Invoice.objects.create(
    pickup_request=pickup,
    base_charge=500.00,
    weight_charge=100.00,
    tax=90.00,
)

# Send email with attachment
send_email_notification(
    pickup_request=pickup,
    notification_type='request_accepted',
    recipient_role='customer',
    invoice=invoice  # Includes PDF attachment
)
```

### 4. Send Email with Custom Reason

```python
# When rejecting with reason
send_email_notification(
    pickup_request=pickup,
    notification_type='request_rejected',
    recipient_role='customer',
    reason='Unable to deliver to this remote area'
)

# When reassigning
send_email_notification(
    pickup_request=pickup,
    notification_type='assignment_reassigned',
    recipient_role='customer',
    reason='Previous driver had mechanical issue'
)
```

### 5. Check Email Status and Handle Response

```python
# Method 1: Check return value
if send_email_notification(pickup, 'driver_assigned', 'driver'):
    messages.success(request, 'Email sent to driver')
else:
    messages.warning(request, 'Email could not be sent')

# Method 2: With logging
try:
    result = send_email_notification(pickup, 'new_request', 'admin')
    if result:
        logger.info(f"Email sent for pickup {pickup.id}")
    else:
        logger.error(f"Email failed for pickup {pickup.id}")
except Exception as e:
    logger.critical(f"Exception: {str(e)}")
```

## Adding Custom Templates

### Step 1: Create Template File

Create `templates/emails/my_custom_email.html`:

```html
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; color: #333; }
        .container { max-width: 600px; margin: 0 auto; border: 1px solid #ddd; }
        .header { background-color: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ subject_line }}</h1>
        </div>
        <div class="content">
            <p>Hi {{ recipient_name }},</p>
            <p>{{ email_body }}</p>
            <p><strong>Tracking Number:</strong> {{ pickup_request.tracking_number }}</p>
        </div>
        <div class="footer">
            <p>&copy; 2024 VRL Logistics</p>
        </div>
    </div>
</body>
</html>
```

### Step 2: Add Configuration

Open `vrllog/utils.py` and add to `_get_email_config()`:

```python
elif notification_type == 'my_custom' and recipient_role == 'customer':
    config = {
        'subject': f'Custom Email - {pickup_request.tracking_number}',
        'recipient_email': pickup_request.customer.email,
        'template_name': 'emails/my_custom_email.html',
        'context': {
            'subject_line': 'Important Notice',
            'recipient_name': pickup_request.customer.first_name,
            'email_body': 'This is a custom email notification.',
            'pickup_request': pickup_request,
        },
        'headers': {}
    }
```

### Step 3: Use in View

```python
send_email_notification(
    pickup_request=pickup,
    notification_type='my_custom',
    recipient_role='customer'
)
```

## Monitoring & Debugging

### 1. Check Email Logs

```bash
# View all email logs
cat vrllogistics/logs/email.log

# Watch logs in real-time
tail -f vrllogistics/logs/email.log

# Count emails sent today
grep "$(date +%Y-%m-%d)" vrllogistics/logs/email.log | wc -l

# Find errors
grep "ERROR" vrllogistics/logs/email.log

# Find specific notification type
grep "assignment_accepted" vrllogistics/logs/email.log
```

### 2. Test Email Configuration

```python
# Django shell
python manage.py shell

# Test basic email
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Subject',
    'Test message',
    settings.DEFAULT_FROM_EMAIL,
    ['recipient@example.com'],
)

# Test with template
from django.template.loader import render_to_string
from vrllog.utils import send_email_notification
from vrllog.models import PickupRequest

pickup = PickupRequest.objects.first()
result = send_email_notification(
    pickup,
    'new_request',
    'admin'
)
print(f"Email sent: {result}")
```

### 3. Debug Email Rendering

```python
from django.template.loader import render_to_string

# Test template rendering
html = render_to_string('emails/my_template.html', {
    'pickup_request': pickup,
    'customer_name': 'John Doe',
})
print(html)

# Check template variables
context = {
    'pickup_request': pickup,
    'customer_name': pickup.customer.first_name,
}
for key, value in context.items():
    print(f"{key}: {value}")
```

## Configuration Reference

### Environment Variables

```bash
# .env file
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
DEFAULT_FROM_EMAIL=your-email@gmail.com
EMAIL_TIMEOUT=10
DEBUG=False
```

### Settings.py Configuration

```python
# Development (console output)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Production (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Email server settings
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 10

# Credentials
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
```

## View Integration Examples

### Admin Dashboard - Accepting Request

```python
@login_required
def admin_accept_request(request, pickup_id):
    pickup = get_object_or_404(PickupRequest, id=pickup_id)
    
    # Update request
    pickup.status = 'accepted'
    pickup.save()
    
    # Create invoice
    invoice = Invoice.objects.create(
        pickup_request=pickup,
        base_charge=500,
        weight_charge=100,
        tax=90,
    )
    
    # Send email with invoice
    try:
        send_email_notification(
            pickup_request=pickup,
            notification_type='request_accepted',
            recipient_role='customer',
            invoice=invoice
        )
        messages.success(request, 'Request accepted and invoice sent')
    except Exception as e:
        logger.error(f"Email failed: {str(e)}")
        messages.warning(request, 'Request accepted but email could not be sent')
    
    return redirect('admin_dashboard')
```

### Driver Dashboard - Accepting Assignment

```python
@login_required
def driver_accept_assignment(request, pickup_id):
    pickup = get_object_or_404(
        PickupRequest,
        id=pickup_id,
        assigned_driver=request.user,
        status='pending_driver_acceptance'
    )
    
    # Update status
    pickup.status = 'assigned'
    pickup.save()
    
    # Send confirmations with error handling
    emails_sent = 0
    try:
        if send_email_notification(
            pickup, 'request_accepted', 'customer'
        ):
            emails_sent += 1
    except Exception as e:
        logger.error(f"Failed to notify customer: {str(e)}")
    
    try:
        if send_email_notification(
            pickup, 'assignment_accepted', 'driver'
        ):
            emails_sent += 1
    except Exception as e:
        logger.error(f"Failed to confirm driver: {str(e)}")
    
    if emails_sent == 2:
        messages.success(request, 'Assignment accepted and confirmations sent')
    else:
        messages.warning(request, f'Assignment accepted but only {emails_sent} emails sent')
    
    return redirect('driver_dashboard')
```

## Template Variables Reference

### Available in All Templates

```django
{{ pickup_request.tracking_number }}
{{ pickup_request.status }}
{{ pickup_request.pickup_date }}
{{ pickup_request.pickup_time }}
{{ pickup_request.customer.first_name }}
{{ pickup_request.customer.last_name }}
{{ pickup_request.customer.email }}
{{ pickup_request.assigned_driver.first_name }}
```

### Sender Information

```django
{{ pickup_request.sender_name }}
{{ pickup_request.sender_email }}
{{ pickup_request.sender_phone }}
{{ pickup_request.sender_address }}
{{ pickup_request.sender_city }}
{{ pickup_request.sender_state }}
{{ pickup_request.sender_zipcode }}
```

### Receiver Information

```django
{{ pickup_request.receiver_name }}
{{ pickup_request.receiver_phone }}
{{ pickup_request.receiver_address }}
{{ pickup_request.receiver_city }}
{{ pickup_request.receiver_state }}
{{ pickup_request.receiver_zipcode }}
```

### Parcel Information

```django
{{ pickup_request.parcel_type }}
{{ pickup_request.parcel_weight }}
{{ pickup_request.parcel_description }}
```

### Invoice Information (if invoice exists)

```django
{{ invoice.invoice_number }}
{{ invoice.issued_date }}
{{ invoice.base_charge }}
{{ invoice.weight_charge }}
{{ invoice.tax }}
{{ invoice.total_amount }}
```

## Logging & Monitoring

### Log Levels

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG - Detailed information for debugging
logger.debug("Email context prepared for pickup 123")

# INFO - General informational messages
logger.info("Email sent successfully to customer@example.com")

# WARNING - Something unexpected, but not critical
logger.warning("Email failed, retrying for pickup 123")

# ERROR - Serious problem
logger.error("Template not found: emails/test.html")

# CRITICAL - System failure
logger.critical("Gmail authentication failed - emails cannot be sent")
```

### Monitoring Email Queue

```bash
# Count emails by type (if you log them)
grep "assignment_accepted" vrllogistics/logs/email.log | wc -l
grep "assignment_reassigned" vrllogistics/logs/email.log | wc -l
grep "driver_assigned" vrllogistics/logs/email.log | wc -l

# Find delivery failures
grep "failed\|error\|Error" vrllogistics/logs/email.log

# Get email statistics
echo "Total emails today:"
grep "$(date +%Y-%m-%d)" vrllogistics/logs/email.log | wc -l
echo "Successful:"
grep "sent successfully" vrllogistics/logs/email.log | wc -l
echo "Failed:"
grep "ERROR" vrllogistics/logs/email.log | wc -l
```

## Troubleshooting Code Examples

### Test 1: Verify Environment Variables

```python
# Django shell
from django.conf import settings

print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"DEBUG: {settings.DEBUG}")
```

### Test 2: Test SMTP Connection

```python
import smtplib
from django.conf import settings

try:
    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    server.starttls()
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    print("✓ SMTP connection successful!")
    server.quit()
except Exception as e:
    print(f"✗ SMTP connection failed: {str(e)}")
```

### Test 3: Test Template Rendering

```python
from django.template.loader import render_to_string
from vrllog.models import PickupRequest

pickup = PickupRequest.objects.first()
try:
    html = render_to_string('emails/driver_assigned.html', {
        'pickup_request': pickup,
        'driver_name': 'John Driver',
    })
    print("✓ Template rendered successfully")
    print(f"HTML length: {len(html)} characters")
except Exception as e:
    print(f"✗ Template rendering failed: {str(e)}")
```

### Test 4: Send Test Email

```python
from vrllog.utils import send_email_notification
from vrllog.models import PickupRequest

pickup = PickupRequest.objects.first()

try:
    result = send_email_notification(
        pickup_request=pickup,
        notification_type='new_request',
        recipient_role='admin'
    )
    if result:
        print("✓ Email sent successfully")
    else:
        print("✗ Email failed - check logs")
except Exception as e:
    print(f"✗ Exception: {str(e)}")
```

## Performance Tips

### 1. Use Async Emails for High Volume

```python
# With Celery
from celery import shared_task

@shared_task
def send_email_async(pickup_id, notification_type, recipient_role):
    from vrllog.models import PickupRequest
    from vrllog.utils import send_email_notification
    
    pickup = PickupRequest.objects.get(id=pickup_id)
    return send_email_notification(
        pickup, notification_type, recipient_role
    )

# In view
send_email_async.delay(pickup.id, 'new_request', 'admin')
```

### 2. Batch Email Sending

```python
from django.core.mail import send_mass_mail

# Prepare list of emails
messages = [
    ('Subject 1', 'Message 1', 'from@example.com', ['to1@example.com']),
    ('Subject 2', 'Message 2', 'from@example.com', ['to2@example.com']),
]

# Send all at once
send_mass_mail(messages, fail_silently=False)
```

### 3. Cache Template Rendering

```python
from django.template.loader import render_to_string
from django.core.cache import cache

def get_template_html(template_name, context):
    cache_key = f"email_template_{template_name}_{hash(str(context))}"
    html = cache.get(cache_key)
    
    if html is None:
        html = render_to_string(template_name, context)
        cache.set(cache_key, html, 3600)  # Cache 1 hour
    
    return html
```

## Complete Integration Checklist

- [ ] Create `.env` file from `.env.example`
- [ ] Fill in Gmail credentials
- [ ] Run `python manage.py check` (no errors)
- [ ] Test email in development with `console.EmailBackend`
- [ ] Test email in production with `smtp.EmailBackend`
- [ ] Check `vrllogistics/logs/email.log` for successful sends
- [ ] Verify email styling in send emails
- [ ] Test with real Gmail account
- [ ] Monitor log file sizes
- [ ] Set up log rotation alerts
- [ ] Document any custom templates
- [ ] Add email monitoring to deployment checks
- [ ] Regular (weekly) review of email logs
- [ ] Document any failures and resolutions

---

For full API documentation, see `EMAIL_SYSTEM_DOCUMENTATION.md`
For implementation details, see `EMAIL_SYSTEM_IMPLEMENTATION.md`