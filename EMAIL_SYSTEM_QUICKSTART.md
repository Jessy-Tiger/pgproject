# Email System - Quick Setup Guide

## 5-Minute Setup

### 1. Copy Environment Template

```bash
cd vrllogistics
cp .env.example .env
```

### 2. Edit .env with Gmail Credentials

Open `vrllogistics/.env`:

```bash
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**How to get Gmail app password:**
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Copy the 16-character password
4. Paste into .env file (spaces are normal)

### 3. Run System Check

```bash
python manage.py check
# Should output: System check identified no issues (0 silenced).
```

### 4. Test Email Sending

**Option A: Development Mode (prints to console)**

```python
# In Django shell
python manage.py shell
>>> from django.core.mail import send_mail
>>> from django.conf import settings
>>> send_mail(
...     'Test Email',
...     'Test message',
...     settings.DEFAULT_FROM_EMAIL,
...     ['test@example.com'],
... )
```

**Option B: Production Mode (sends real emails)**

Create a test script `test_email.py`:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vrllogistics.settings')
django.setup()

from vrllog.models import PickupRequest
from vrllog.utils import send_email_notification

# Get first pickup request
pickup = PickupRequest.objects.first()

if pickup:
    result = send_email_notification(
        pickup,
        'new_request',
        'admin'
    )
    print(f"Email sent: {result}")
else:
    print("No pickup requests found")
```

Run it:
```bash
python test_email.py
```

### 5. Verify Email Logs

```bash
# Check if email was sent
tail -f vrllogistics/logs/email.log

# Should show: "Email sent successfully: ..."
```

## What Was Changed

### Files Modified ✅

| File | Change | Impact |
|------|--------|--------|
| `utils.py` | Complete refactor | Better error handling, logging |
| `settings.py` | Added logging, config | Environment variables, audit trail |
| `views.py` | Added try-catch blocks | Emails won't break workflows |
| `templates/emails/*` | 3 new templates | Proper HTML for all notification types |
| `.env.example` | Created | Security best practices |

### Files Created ✅

1. `templates/emails/assignment_accepted_driver.html` - Driver confirmation
2. `templates/emails/assignment_reassigned_customer.html` - Reassignment notice
3. `templates/emails/assignment_waiting_customer.html` - Waiting status
4. `.env.example` - Configuration template
5. `EMAIL_SYSTEM_DOCUMENTATION.md` - Full documentation (600+ lines)
6. `EMAIL_SYSTEM_IMPLEMENTATION.md` - Implementation details
7. `EMAIL_SYSTEM_EXAMPLES.md` - Code examples
8. `EMAIL_SYSTEM_QUICKSTART.md` - This file

### Directories Created ✅

- `logs/` - Auto-created for email logging
  - `email.log` - Email activities
  - `django.log` - Framework warnings
  - `error.log` - Critical errors

## Key Improvements

### 1. Security
- ✅ Credentials in `.env` (not hardcoded)
- ✅ Environment-driven configuration
- ✅ No passwords in source code

### 2. Reliability
- ✅ Offline email failures don't break requests
- ✅ Proper exception handling throughout
- ✅ Defensive programming patterns

### 3. Maintainability
- ✅ Code split into small functions
- ✅ Template-based HTML (no inline strings)
- ✅ Clear separation of concerns
- ✅ Easy to add new notification types

### 4. Debugging
- ✅ Comprehensive logging
- ✅ Separate log files for different components
- ✅ Rotating file handlers prevent disk issues
- ✅ Easy to find and debug problems

### 5. Scalability
- ✅ Ready for async email (Celery)
- ✅ Template caching ready
- ✅ Batch email support
- ✅ Log rotation built-in

## Notification Types

| Type | Sent To | When | Template |
|------|---------|------|----------|
| new_request | Admin | Customer creates request | ✓ |
| request_accepted | Customer | Admin accepts | ✓ + PDF |
| request_rejected | Customer | Admin rejects | ✓ |
| driver_assigned | Driver | Assigned to request | ✓ |
| status_update | Customer | Status changes | ✓ |
| assignment_accepted | Driver | Driver accepts | ✓ NEW |
| assignment_reassigned | Customer | Reassigned after reject | ✓ NEW |
| assignment_waiting | Customer | No drivers available | ✓ NEW |

## Common Tasks

### Test Email System

```bash
# Check configuration
python manage.py check

# View settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.EMAIL_BACKEND)

# Monitor emails in real-time
tail -f vrllogistics/logs/email.log
```

### Add New Notification Type

1. Create template: `templates/emails/my_template.html`
2. Add config in `utils.py` `_get_email_config()` function
3. Call from view: `send_email_notification(..., 'my_type', ...)`
4. Check logs: `grep "my_type" vrllogistics/logs/email.log`

### Debug Email Failure

```bash
# Find the error
grep "ERROR" vrllogistics/logs/email.log

# Get more context
tail -20 vrllogistics/logs/email.log

# Search by pickup ID
grep "pickup_123" vrllogistics/logs/email.log
```

### Monitor Performance

```bash
# Count emails sent today
grep "$(date +%Y-%m-%d)" vrllogistics/logs/email.log | wc -l

# Count by type
grep "new_request" vrllogistics/logs/email.log | wc -l
grep "request_accepted" vrllogistics/logs/email.log | wc -l

# Check success rate
TOTAL=$(grep "$(date +%Y-%m-%d)" vrllogistics/logs/email.log | wc -l)
SUCCESS=$(grep "sent successfully" vrllogistics/logs/email.log | wc -l)
echo "Success rate: $((SUCCESS * 100 / TOTAL))%"
```

## Troubleshooting

### Email Not Sending?

```bash
# Check logs first
tail -20 vrllogistics/logs/email.log

# Common issues:
grep "ERROR\|failed\|Connection" vrllogistics/logs/email.log

# Check configuration
python manage.py shell
>>> from django.conf import settings
>>> print(f"User: {settings.EMAIL_HOST_USER}")
>>> print(f"Host: {settings.EMAIL_HOST}")
>>> print(f"Port: {settings.EMAIL_PORT}")
```

### "Template not found"

```bash
# Check template exists
ls templates/emails/

# Check template name is correct
grep "template_name" vrllog/utils.py | grep "your_template"
```

### "Authentication failed"

```bash
# Regenerate app password at:
# https://myaccount.google.com/apppasswords

# Update .env
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx

# Test again
python manage.py test
```

### "Timeout" or "Connection refused"

```bash
# Check EMAIL_HOST and EMAIL_PORT
python manage.py shell
>>> from django.conf import settings
>>> settings.EMAIL_HOST  # Should be smtp.gmail.com
>>> settings.EMAIL_PORT  # Should be 587

# Test SMTP connection
python manage.py shell
>>> import smtplib
>>> server = smtplib.SMTP('smtp.gmail.com', 587)
>>> server.starttls()
>>> # If this worked, connection is good
```

## File Structure

```
vrllogistics/ (project root)
├── vrllog/
│   ├── utils.py ......................... ✅ Email system (refactored)
│   ├── views.py ......................... ✅ Error handling (updated)
│   └── models.py ........................ (no changes)
├── vrllogistics/
│   └── settings.py ...................... ✅ Email config (enhanced)
├── templates/
│   └── emails/
│       ├── new_request_admin.html ........ (existing)
│       ├── request_accepted_customer.html  (existing)
│       ├── request_rejected_customer.html  (existing)
│       ├── driver_assigned.html ......... (existing)
│       ├── status_update_customer.html .. (existing)
│       ├── assignment_accepted_driver.html (NEW) ✅
│       ├── assignment_reassigned_customer.html (NEW) ✅
│       └── assignment_waiting_customer.html (NEW) ✅
├── logs/ (auto-created)
│   ├── email.log ........................ ✅ Email activities
│   ├── django.log ....................... ✅ Framework logging
│   └── error.log ........................ ✅ Error logging
└── .env.example ......................... ✅ Configuration template
```

## Next Steps

### Immediate (After Setup)

1. ✅ Create `.env` file from `.env.example`
2. ✅ Add Gmail credentials to `.env`
3. ✅ Run `python manage.py check`
4. ✅ Test email with `send_mail()`
5. ✅ Check `logs/email.log` for results

### Short-term (This Week)

1. ✅ Test all email notification types
2. ✅ Verify styling looks good
3. ✅ Check spam folders
4. ✅ Monitor logs for errors
5. ✅ Document any issues

### Medium-term (This Month)

1. ✅ Set up automated log monitoring
2. ✅ Consider async emails with Celery
3. ✅ Add email analytics/tracking
4. ✅ Review and update templates with branding
5. ✅ Test with real customers

### Long-term (Ongoing)

1. ✅ Monitor email delivery rates
2. ✅ Review logs weekly
3. ✅ Update templates as needed
4. ✅ Plan for high-volume handling
5. ✅ Consider external email service

## Production Deployment Checklist

Before going live:

- [ ] All credentials in `.env` (not in code)
- [ ] `.env` added to `.gitignore`
- [ ] `DEBUG = False` in settings.py
- [ ] Email tested with real Gmail account
- [ ] All notification types tested
- [ ] Log rotation working
- [ ] Logs monitored (manual or automated)
- [ ] Error handling tested (network fail, etc.)
- [ ] Templates reviewed for branding
- [ ] Fallback sender configured
- [ ] Admin notifications working
- [ ] Reply-to headers set correctly

## Support Documentation

For more details, see:

1. **EMAIL_SYSTEM_DOCUMENTATION.md** - Complete 600+ line guide
2. **EMAIL_SYSTEM_IMPLEMENTATION.md** - What changed and why
3. **EMAIL_SYSTEM_EXAMPLES.md** - Code examples and patterns
4. **This file** - Quick setup and common tasks

## Quick Reference

```bash
# View email logs
tail -f vrllogistics/logs/email.log

# Test email config
python manage.py check

# Run Django shell
python manage.py shell

# Count emails sent
grep "sent successfully" vrllogistics/logs/email.log | wc -l

# Find errors
grep "ERROR" vrllogistics/logs/email.log

# Monitor in real-time
watch "tail -10 vrllogistics/logs/email.log"
```

## Dashboard Monitoring (Optional)

For production, consider setting up:

1. **Log Aggregation**: ELK Stack, Splunk, DataDog
2. **Email Monitoring**: SendGrid, Mandrill, Mailgun
3. **Alerts**: PagerDuty, Opsgenie, Slack notifications
4. **Analytics**: Email delivery rates, bounce rates
5. **Backups**: Automated log backups and archival

## Getting Help

1. Check logs: `vrllogistics/logs/email.log`
2. Read documentation: `EMAIL_SYSTEM_DOCUMENTATION.md`
3. Try code examples: `EMAIL_SYSTEM_EXAMPLES.md`
4. Test manually: Use Django shell
5. Common issues: See "Troubleshooting" section above

---

**Everything is ready to go!** The email system is production-grade with proper:
- ✅ Configuration management
- ✅ Error handling
- ✅ Logging
- ✅ Security
- ✅ Documentation

Start using the system and monitor `logs/email.log` for any issues.