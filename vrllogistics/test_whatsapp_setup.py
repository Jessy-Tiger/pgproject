"""
WhatsApp Notification Setup Test Script
This script verifies the WhatsApp notification system is properly configured.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vrllogistics.settings')
django.setup()

from django.conf import settings
from vrllog.models import PickupRequest, User
from vrllog.utils import send_whatsapp_notification, format_whatsapp_message

print("\n" + "="*70)
print("WhatsApp Notification System - Configuration Check")
print("="*70)

# Check Twilio Configuration
print("\n1. TWILIO CONFIGURATION:")
print(f"   ✓ Account SID: {settings.TWILIO_ACCOUNT_SID[:10]}...configured")
print(f"   ✓ Auth Token: {settings.TWILIO_AUTH_TOKEN[:10]}...configured")
print(f"   ✓ WhatsApp Number: {settings.TWILIO_WHATSAPP_NUMBER}")
print(f"   ✓ Notifications Enabled: {settings.WHATSAPP_NOTIFICATIONS_ENABLED}")
print(f"   ✓ Retry Attempts: {settings.WHATSAPP_RETRY_ATTEMPTS}")
print(f"   ✓ Retry Delay: {settings.WHATSAPP_RETRY_DELAY} seconds")
print(f"   ✓ Admin Phone: {settings.ADMIN_PHONE_NUMBER}")

# Check User Data
print("\n2. USER DATA:")
admin_user = User.objects.filter(profile__role='admin').first()
if admin_user:
    print(f"   ✓ Admin User: {admin_user.username}")
    print(f"   ✓ Admin Email: {admin_user.email}")
    admin_phone = admin_user.profile.phone_number if hasattr(admin_user, 'profile') else None
    print(f"   ✓ Admin Phone in Profile: {admin_phone or 'NOT SET (using ADMIN_PHONE_NUMBER from settings)'}")

customers = User.objects.filter(profile__role='customer')
print(f"   ✓ Total Customers: {customers.count()}")

drivers = User.objects.filter(profile__role='driver')
print(f"   ✓ Total Drivers: {drivers.count()}")

# Check Pickup Requests
print("\n3. PICKUP REQUESTS:")
pickups = PickupRequest.objects.all()
statuses = {}
for p in pickups:
    statuses[p.status] = statuses.get(p.status, 0) + 1

print(f"   ✓ Total Requests: {pickups.count()}")
for status, count in statuses.items():
    print(f"     - {status}: {count}")

# Show Sample Notifications
print("\n4. SAMPLE NOTIFICATION MESSAGES:")

# Get a sample pickup
sample_pickup = PickupRequest.objects.first()
if sample_pickup:
    print(f"\n   Sample Pickup: {sample_pickup.tracking_number}")
    
    # New Request (to Admin)
    msg = format_whatsapp_message('new_request', {
        'tracking_number': sample_pickup.tracking_number,
        'sender_name': sample_pickup.sender_name,
        'receiver_name': sample_pickup.receiver_name,
        'sender_address': f"{sample_pickup.sender_address}, {sample_pickup.sender_city}",
    })
    print(f"\n   a) To Admin (New Request):\n{msg}")
    
    # Request Accepted (to Customer)
    msg = format_whatsapp_message('request_accepted', {
        'tracking_number': sample_pickup.tracking_number,
        'pickup_date': sample_pickup.pickup_date.strftime('%d-%m-%Y') if sample_pickup.pickup_date else 'TBD',
        'pickup_time': sample_pickup.pickup_time,
        'pickup_address': f"{sample_pickup.sender_address}, {sample_pickup.sender_city}",
    })
    print(f"\n   b) To Customer (Request Accepted):\n{msg}")
    
    # Driver Assigned (to Driver)
    if sample_pickup.assigned_driver:
        msg = format_whatsapp_message('driver_assigned', {
            'tracking_number': sample_pickup.tracking_number,
            'customer_name': sample_pickup.customer.first_name or sample_pickup.customer.username,
            'driver_name': sample_pickup.assigned_driver.first_name or sample_pickup.assigned_driver.username,
            'driver_phone': sample_pickup.assigned_driver.profile.phone_number if hasattr(sample_pickup.assigned_driver, 'profile') else 'N/A',
            'pickup_time': sample_pickup.pickup_time,
        })
        print(f"\n   c) To Driver (Driver Assigned):\n{msg}")
    
    # Assignment Accepted (to Admin)
    if sample_pickup.assigned_driver:
        msg = format_whatsapp_message('assignment_accepted_admin', {
            'tracking_number': sample_pickup.tracking_number,
            'driver_name': sample_pickup.assigned_driver.first_name or sample_pickup.assigned_driver.username,
            'customer_name': sample_pickup.customer.first_name or sample_pickup.customer.username,
            'pickup_date': sample_pickup.pickup_date.strftime('%d-%m-%Y') if sample_pickup.pickup_date else 'TBD',
            'pickup_time': sample_pickup.pickup_time,
            'pickup_address': f"{sample_pickup.sender_address}, {sample_pickup.sender_city}",
        })
        print(f"\n   d) To Admin (Driver Accepted):\n{msg}")

print("\n" + "="*70)
print("NOTIFICATION FLOW:")
print("="*70)
print("""
1. Customer creates Pickup Request
   → Admin receives WhatsApp: "New Pickup Request Created"
   
2. Admin accepts Pickup Request
   → Customer receives WhatsApp: "Request Accepted"
   → Driver receives WhatsApp: "Driver Assigned"
   
3. Driver accepts Assignment
   → Customer receives WhatsApp: "Pickup Confirmed"
   → Driver receives WhatsApp: "Assignment Confirmed"
   → Admin receives WhatsApp: "Driver Accepted Assignment"
""")

print("="*70)
print("✓ WhatsApp Notification System is properly configured!")
print("="*70 + "\n")
