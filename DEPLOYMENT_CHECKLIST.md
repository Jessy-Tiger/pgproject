# WhatsApp System Deployment Checklist

Complete this checklist to deploy the WhatsApp notification system.

---

## Phase 1: Pre-Deployment (Local Development)

### Code Review
- [ ] Read `IMPLEMENTATION_REPORT.md` for overview
- [ ] Review all changes in `utils.py`
- [ ] Verify all 11 view updates are correct
- [ ] Check `.env.example` has Twilio variables
- [ ] Confirm email templates folder deleted

### Local Setup
- [ ] Python 3.8+ installed
- [ ] Virtual environment activated: `source ms/Scripts/activate`
- [ ] Install Twilio SDK: `pip install twilio`
- [ ] Run system check: `python manage.py check`
  - Expected: `System check identified no issues (0 silenced)`
- [ ] Create logs directory: `mkdir -p vrllogistics/logs`

### Local Configuration
- [ ] Copy .env.example to .env: `cp .env.example .env`
- [ ] Open .env file for editing
- [ ] Set DEBUG=True (for development)

### Twilio Account Setup
- [ ] Sign up at https://www.twilio.com/console
- [ ] Verify email and phone number
- [ ] Copy Account SID from console
- [ ] Copy Auth Token from console (generate if needed)
- [ ] Set up WhatsApp Sandbox:
  - [ ] Go to Messaging → Services
  - [ ] Create Messaging Service
  - [ ] Add WhatsApp channel
  - [ ] Join sandbox (save sandbox number)
- [ ] Add your phone to sandbox:
  - [ ] Send "join YOUR_CODE" to sandbox number
  - [ ] Confirm on WhatsApp app

### Local Testing
- [ ] Add credentials to .env:
  ```
  TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxx
  TWILIO_AUTH_TOKEN=yyyyyyyyyyyyyyyyyy
  TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
  ```
- [ ] Test message in Django shell:
  ```bash
  python manage.py shell
  >>> from vrllog.utils import send_whatsapp_message
  >>> send_whatsapp_message('+91YOUR_PHONE', 'Test!')
  >>> exit()
  ```
- [ ] Check you received the WhatsApp message
- [ ] Check logs: `cat vrllogistics/logs/whatsapp.log`
- [ ] Verify message appears in log

---

## Phase 2: Testing (Staging Environment)

### Create Test Data
- [ ] Create test customer account
- [ ] Create test driver account
- [ ] Add phone numbers to profiles
- [ ] Ensure phone numbers in format: +91XXXXXXXXXX

### Test Notification Flow
- [ ] Customer creates pickup request
  - [ ] Check admin receives WhatsApp ✅
  - [ ] Check log shows "sent successfully"
  
- [ ] Admin accepts request
  - [ ] Check customer receives WhatsApp ✅
  - [ ] Check driver receives WhatsApp ✅
  
- [ ] Driver accepts assignment
  - [ ] Check driver receives confirmation ✅
  - [ ] Check log shows both sends

- [ ] Admin rejects request
  - [ ] Check customer receives rejection ✅
  - [ ] Check log shows error handling

### Monitor Logs
- [ ] View real-time logs: `tail -f vrllogistics/logs/whatsapp.log`
- [ ] Check error logs: `tail -f vrllogistics/logs/error.log`
- [ ] Count success messages: 
  ```bash
  grep "sent successfully" vrllogistics/logs/whatsapp.log | wc -l
  ```
- [ ] Count failed messages:
  ```bash
  grep "Failed to send" vrllogistics/logs/whatsapp.log | wc -l
  ```

### User Acceptance Testing
- [ ] Customer creates pickup, receives notification immediately
- [ ] Admin processes request, receives notifications
- [ ] Driver accepts/rejects assignment, gets updates
- [ ] All messages formatted correctly with emojis
- [ ] Phone numbers handled correctly

### Performance Testing
- [ ] Create 10 test pickups quickly
- [ ] Verify all notifications sent
- [ ] Check no message delays
- [ ] Monitor logs for errors
- [ ] Verify logs not growing too large

---

## Phase 3: Production Preparation

### Upgrade Twilio Account
- [ ] Upgrade from Sandbox to Production
- [ ] Apply for WhatsApp Business Account
- [ ] Register business number
- [ ] Get production phone number
- [ ] Get API credentials for production

### Production Configuration
- [ ] Create production `.env` file
- [ ] Add production TWILIO credentials
- [ ] Set WHATSAPP_NOTIFICATIONS_ENABLED=True
- [ ] Set appropriate RETRY settings
- [ ] Set ADMIN_PHONE_NUMBER for alerts

### Production Infrastructure
- [ ] Create logs directory with proper permissions
- [ ] Set up log rotation (optional):
  ```bash
  # Install logrotate or equivalent
  # Rotate logs daily, keep last 30 days
  ```
- [ ] Set up monitoring/alerts:
  - [ ] Alert if failure rate > 5%
  - [ ] Alert if Twilio account balance low
  - [ ] Alert if auth token about to expire
- [ ] Create database backup automation
- [ ] Set up log aggregation (optional)

### Security Hardening
- [ ] Ensure .env is in .gitignore
- [ ] Verify no secrets in code
- [ ] Enable HTTPS for all endpoints
- [ ] Set up IP whitelisting if applicable
- [ ] Configure firewall rules
- [ ] Rotate Twilio auth token if older than 6 months

---

## Phase 4: Production Deployment

### Pre-Deployment Checklist
- [ ] Database backed up
- [ ] Code reviewed and tested
- [ ] All logs configured
- [ ] Monitoring setup complete
- [ ] Team trained on troubleshooting
- [ ] Rollback plan documented

### Deployment Steps
1. [ ] Deploy code to production server
2. [ ] Verify Django check passes
3. [ ] Update production `.env` with credentials
4. [ ] Create logs directory: `mkdir -p vrllogistics/logs`
5. [ ] Set permissions: `chmod 755 vrllogistics/logs`
6. [ ] Restart Django/application server
7. [ ] Run final system check: `python manage.py check`

### Post-Deployment Verification
- [ ] Site loads without errors
- [ ] All pages accessible
- [ ] Django admin works
- [ ] Create test pickup request
- [ ] Verify WhatsApp notification received
- [ ] Check logs updated: `tail -f vrllogistics/logs/whatsapp.log`
- [ ] Monitor for first 24 hours

### Production Monitoring (First Week)
- [ ] Monitor failure rate (target: <2%)
- [ ] Check delivery times (target: <5 seconds)
- [ ] Verify no crashes
- [ ] Watch for unusual patterns in logs
- [ ] Monitor Twilio account for issues
- [ ] Gather user feedback

---

## Phase 5: Post-Deployment

### Ongoing Maintenance
- [ ] Daily: Check error logs
- [ ] Weekly: Review WhatsApp logs for patterns
- [ ] Monthly: Review Twilio account usage
- [ ] Quarterly: Audit phone numbers in database

### Monitoring Dashboard (Recommended)
Create a simple dashboard to track:
```
- Messages sent today
- Messages failed today
- Failure rate percentage
- Average delivery time
- Top notification types
- Failed recipient phone numbers
```

### Scheduled Tasks (Recommended)
```bash
# Daily backup at 2 AM
0 2 * * * python manage.py dumpdata > /backup/django_$(date +\%Y\%m\%d).json

# Daily log rotation at 11 PM
0 23 * * * gzip vrllogistics/logs/whatsapp.log

# Weekly report (Monday 9 AM)
0 9 * * 1 python scripts/whatsapp_report.py
```

### Update Plan
- [ ] Subscribe to Twilio security updates
- [ ] Monitor Django security releases
- [ ] Review Twilio changelog quarterly
- [ ] Test major Django updates in staging first

---

## Rollback Plan (If Issues)

If something goes wrong, execute this to revert:

1. [ ] Stop receiving new requests (maintenance mode)
2. [ ] Switch notifications back to email (if needed):
   ```bash
   git revert <commit_hash>
   python manage.py migrate
   restart_application
   ```
3. [ ] Verify system still works
4. [ ] Investigate issue in staging
5. [ ] Fix and test thoroughly
6. [ ] Re-deploy to production

---

## Common Issues During Deployment

### Issue: "Twilio library not found"
- [ ] Run: `pip install twilio`
- [ ] Verify: `python -c "from twilio.rest import Client; print('OK')"`

### Issue: "Invalid credentials"
- [ ] Double-check Account SID (copy exactly from console)
- [ ] Double-check Auth Token (generate new if unsure)
- [ ] Restart application after updating .env

### Issue: "Messages not sending"
- [ ] Check phone numbers are in format +91XXXXXXXXXX
- [ ] Verify TWILIO_WHATSAPP_NUMBER is correct
- [ ] Ensure WhatsApp app is installed on test phone
- [ ] Check Twilio account isn't suspended
- [ ] Review whatsapp.log for error details

### Issue: "High failure rate"
- [ ] Review phone numbers for invalid formats
- [ ] Check Twilio account balance
- [ ] Verify no rate limiting issues
- [ ] Check network connectivity
- [ ] Review error logs for patterns

---

## Success Criteria

✅ **Deployment is successful if:**
- [ ] All notification types working
- [ ] Messages arrive in <5 seconds
- [ ] Failure rate < 2%
- [ ] No application crashes
- [ ] Logs generated correctly
- [ ] Team can troubleshoot issues
- [ ] Users receiving timely updates

---

## Documentation References

Before deployment, read:
1. **Setup Guide:** [WHATSAPP_SETUP.md](./WHATSAPP_SETUP.md) - 400 lines
2. **Implementation Report:** [IMPLEMENTATION_REPORT.md](./IMPLEMENTATION_REPORT.md) - Overview
3. **Quick Reference:** [WHATSAPP_QUICK_REFERENCE.md](./WHATSAPP_QUICK_REFERENCE.md) - Developer guide
4. **Migration Summary:** [MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md) - Changes made

---

## Estimated Timeline

| Phase | Timeline | Status |
|-------|----------|--------|
| Pre-Deployment (Local) | 1-2 hours | ⏳ Start here |
| Testing (Staging) | 1-2 days | ⏳ After local works |
| Production Prep | 1-2 days | ⏳ Before go-live |
| Deployment | 30 minutes | ⏳ When ready |
| Monitoring | 1 week | ⏳ After deploy |

---

## Support Contact

If stuck at any point:
1. Check relevant documentation file (above)
2. Check logs: `vrllogistics/logs/whatsapp.log`
3. Run: `python manage.py check`
4. Test in Django shell for debugging
5. Contact VRL Logistics Development Team

---

## Sign-Off

- [ ] All phases complete
- [ ] System validated
- [ ] Team trained
- [ ] Documentation reviewed
- [ ] Ready for production

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Verified By:** _______________  

---

**Good luck! 🚀**

Your VRL Logistics WhatsApp notification system is ready to launch!
