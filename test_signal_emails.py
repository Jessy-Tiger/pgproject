#!/usr/bin/env python
"""
Signal Email Notification System - Verification Script

This script tests all 4 workflows of the signal-based email notification system.
Run from Django shell:
  python manage.py shell
  exec(open('test_signal_emails.py').read())
"""

import sys
from django.contrib.auth.models import User
from vrllog.models import PickupRequest, UserProfile
from django.utils import timezone
from datetime import timedelta

print("\n" + "="*80)
print("SIGNAL EMAIL NOTIFICATION SYSTEM - VERIFICATION TEST")
print("="*80)

# Create test customer if not exists
customer_user, _ = User.objects.get_or_create(
    username='test_customer',
    defaults={
        'email': 'customer@test.com',
        'first_name': 'Test',
        'last_name': 'Customer'
    }
)

# Ensure profile exists
customer_profile, _ = UserProfile.objects.get_or_create(
    user=customer_user,
    defaults={'role': 'customer'}
)

# Create test driver if not exists
driver_user, _ = User.objects.get_or_create(
    username='test_driver',
    defaults={
        'email': 'driver@test.com',
        'first_name': 'Test',
        'last_name': 'Driver'
    }
)

# Ensure profile exists
driver_profile, _ = UserProfile.objects.get_or_create(
    user=driver_user,
    defaults={'role': 'driver'}
)

print("\n📋 TEST SETUP COMPLETE")
print(f"   Customer: {customer_user.username} ({customer_user.email})")
print(f"   Driver: {driver_user.username} ({driver_user.email})")

# ============================================================================
# WORKFLOW 1: NEW REQUEST → ADMIN EMAIL
# ============================================================================
print("\n" + "-"*80)
print("TEST 1: WORKFLOW 1 - NEW REQUEST (Should email ADMIN)")
print("-"*80)

try:
    pickup_1 = PickupRequest.objects.create(
        customer=customer_user,
        sender_name="Test Sender",
        sender_phone="9876543210",
        sender_address="123 Test Street",
        sender_city="Test City",
        sender_state="Test State",
        sender_zipcode="123456",
        receiver_name="Test Receiver",
        receiver_phone="9876543211",
        receiver_address="456 Test Avenue",
        receiver_city="Another City",
        receiver_state="Another State",
        receiver_zipcode="654321",
        parcel_type="documents",
        parcel_weight=2.5,
        pickup_date=timezone.now().date() + timedelta(days=1),
        pickup_time="10:00:00"
    )
    print(f"✅ TEST 1 COMPLETE: Pickup #{pickup_1.id} created")
    print(f"   Expected: Email sent to ADMIN")
    print(f"   Status: {pickup_1.status}")
    TEST_1_ID = pickup_1.id
except Exception as e:
    print(f"❌ TEST 1 FAILED: {str(e)}")
    sys.exit(1)

# ============================================================================
# WORKFLOW 2: PENDING → ACCEPTED (Should email CUSTOMER + DRIVER)
# ============================================================================
print("\n" + "-"*80)
print("TEST 2: WORKFLOW 2 - ACCEPT REQUEST (Should email CUSTOMER + DRIVER)")
print("-"*80)

try:
    pickup_2 = PickupRequest.objects.create(
        customer=customer_user,
        sender_name="Test Sender 2",
        sender_phone="9876543210",
        sender_address="123 Test Street",
        sender_city="Test City",
        sender_state="Test State",
        sender_zipcode="123456",
        receiver_name="Test Receiver 2",
        receiver_phone="9876543211",
        receiver_address="456 Test Avenue",
        receiver_city="Another City",
        receiver_state="Another State",
        receiver_zipcode="654321",
        parcel_type="electronics",
        parcel_weight=5.0,
        pickup_date=timezone.now().date() + timedelta(days=1),
        pickup_time="14:00:00"
    )
    
    # Now accept it
    pickup_2.status = 'accepted'
    pickup_2.assigned_driver = driver_user
    pickup_2.save()
    
    print(f"✅ TEST 2 COMPLETE: Pickup #{pickup_2.id} accepted with driver assignment")
    print(f"   Previous Status: pending")
    print(f"   Current Status: {pickup_2.status}")
    print(f"   Assigned Driver: {driver_user.username}")
    print(f"   Expected: Email sent to CUSTOMER + DRIVER")
    TEST_2_ID = pickup_2.id
except Exception as e:
    print(f"❌ TEST 2 FAILED: {str(e)}")
    sys.exit(1)

# ============================================================================
# WORKFLOW 3: PENDING → REJECTED (Should email CUSTOMER only)
# ============================================================================
print("\n" + "-"*80)
print("TEST 3: WORKFLOW 3 - REJECT REQUEST (Should email CUSTOMER)")
print("-"*80)

try:
    pickup_3 = PickupRequest.objects.create(
        customer=customer_user,
        sender_name="Test Sender 3",
        sender_phone="9876543210",
        sender_address="123 Test Street",
        sender_city="Test City",
        sender_state="Test State",
        sender_zipcode="123456",
        receiver_name="Test Receiver 3",
        receiver_phone="9876543211",
        receiver_address="456 Test Avenue",
        receiver_city="Another City",
        receiver_state="Another State",
        receiver_zipcode="654321",
        parcel_type="fragile",
        parcel_weight=3.0,
        pickup_date=timezone.now().date() + timedelta(days=1),
        pickup_time="16:00:00"
    )
    
    # Now reject it
    pickup_3.status = 'rejected'
    pickup_3.save()
    
    print(f"✅ TEST 3 COMPLETE: Pickup #{pickup_3.id} rejected")
    print(f"   Previous Status: pending")
    print(f"   Current Status: {pickup_3.status}")
    print(f"   Expected: Email sent to CUSTOMER ONLY")
    TEST_3_ID = pickup_3.id
except Exception as e:
    print(f"❌ TEST 3 FAILED: {str(e)}")
    sys.exit(1)

# ============================================================================
# WORKFLOW 4: DRIVER STATUS UPDATES (Should email CUSTOMER + ADMIN)
# ============================================================================
print("\n" + "-"*80)
print("TEST 4: WORKFLOW 4 - DRIVER STATUS UPDATE (Should email CUSTOMER + ADMIN)")
print("-"*80)

try:
    pickup_4 = PickupRequest.objects.create(
        customer=customer_user,
        sender_name="Test Sender 4",
        sender_phone="9876543210",
        sender_address="123 Test Street",
        sender_city="Test City",
        sender_state="Test State",
        sender_zipcode="123456",
        receiver_name="Test Receiver 4",
        receiver_phone="9876543211",
        receiver_address="456 Test Avenue",
        receiver_city="Another City",
        receiver_state="Another State",
        receiver_zipcode="654321",
        parcel_type="perishable",
        parcel_weight=1.5,
        pickup_date=timezone.now().date() + timedelta(days=1),
        pickup_time="09:00:00",
        status='accepted',
        assigned_driver=driver_user
    )
    
    # Test picked_up
    print(f"\n   4a. Testing picked_up status...")
    pickup_4.status = 'picked_up'
    pickup_4.save()
    print(f"      ✓ Pickup #{pickup_4.id} marked as picked_up")
    
    # Test in_transit
    print(f"\n   4b. Testing in_transit status...")
    pickup_4.status = 'in_transit'
    pickup_4.save()
    print(f"      ✓ Pickup #{pickup_4.id} marked as in_transit")
    
    # Test delivered
    print(f"\n   4c. Testing delivered status...")
    pickup_4.status = 'delivered'
    pickup_4.completed_at = timezone.now()
    pickup_4.save()
    print(f"      ✓ Pickup #{pickup_4.id} marked as delivered")
    
    print(f"\n✅ TEST 4 COMPLETE: Driver status updates tested")
    print(f"   Expected: Email sent to CUSTOMER + ADMIN for each status change")
    TEST_4_ID = pickup_4.id
except Exception as e:
    print(f"❌ TEST 4 FAILED: {str(e)}")
    sys.exit(1)

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
print("="*80)

print("\n📊 TEST SUMMARY:")
print(f"   Workflow 1 (New Request): Pickup #{TEST_1_ID}")
print(f"   Workflow 2 (Accept): Pickup #{TEST_2_ID}")
print(f"   Workflow 3 (Reject): Pickup #{TEST_3_ID}")
print(f"   Workflow 4 (Status Update): Pickup #{TEST_4_ID}")

print("\n📋 VERIFICATION CHECKLIST:")
print("   [ ] Saw 'SIGNALS MODULE LOADED' message on server startup")
print("   [ ] Saw '🔔 SIGNAL TRIGGERED' messages above for each test")
print("   [ ] Saw workflow trigger messages (WORKFLOW 1, 2, 3, 4)")
print("   [ ] Check email inbox for test emails (if SMTP configured)")
print("   [ ] Check logs in vrllogistics/logs/ directory")

print("\n💡 NEXT STEPS:")
print("   1. Check console output for signal debug messages")
print("   2. Check vrllogistics/logs/django.log for detailed logs")
print("   3. Check email inbox for notifications")
print("   4. If no emails: verify EMAIL_NOTIFICATIONS_ENABLED=True in settings")
print("   5. If no console output: verify DEBUG=True in settings")

print("\n" + "="*80)
print("TEST COMPLETED - Check console output above ↑")
print("="*80 + "\n")
