"""
PRODUCTION-GRADE Email Notification System for VRL Logistics

Implements strict, state-aware email triggers with:
- Previous state tracking to prevent duplicate emails
- Precise status detection before sending
- Clean separation of concerns
- Comprehensive logging and error handling
- Zero unintended side effects

PickupRequest Lifecycle:
1. pending → NEW REQUEST created → Email ADMIN only
2. pending → accepted → EMAIL TO CUSTOMER + DRIVER (if assigned)
3. pending → rejected → EMAIL TO CUSTOMER only
4. picked_up/in_transit/delivered → EMAIL TO ADMIN + CUSTOMER
"""

import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import PickupRequest
from .email_service import send_notification_email
from django.conf import settings

logger = logging.getLogger(__name__)

# Store previous state in memory to track changes
_pickup_previous_state = {}


@receiver(pre_save, sender=PickupRequest)
def track_pickup_changes(sender, instance, **kwargs):
    """
    PRE-SAVE: Store the old state of the pickup request before changes.
    
    This is CRITICAL for detecting state changes and preventing:
    - Duplicate emails on repeated saves
    - Emails triggered on unrelated field updates
    - Incorrect recipient detection
    
    Strategy: Store old state keyed by instance.id
    """
    try:
        # Only track if the instance already exists in DB
        if instance.id:
            old_instance = PickupRequest.objects.filter(id=instance.id).first()
            
            if old_instance:
                _pickup_previous_state[instance.id] = {
                    'status': old_instance.status,
                    'assigned_driver': old_instance.assigned_driver_id,
                }
                logger.debug(
                    f"[TRACK] Pickup #{instance.id}: "
                    f"status {old_instance.status} → {instance.status}, "
                    f"driver {old_instance.assigned_driver_id} → {instance.assigned_driver_id}"
                )
        else:
            # New instance - nothing to track
            _pickup_previous_state.pop(instance.id, None)
            
    except Exception as e:
        logger.error(f"Error tracking pickup state changes: {str(e)}", exc_info=True)


@receiver(post_save, sender=PickupRequest)
def send_email_notifications(sender, instance, created, update_fields, **kwargs):
    """
    POST-SAVE: Send emails based on state changes.
    
    WORKFLOW:
    1. NEW REQUEST (instance.created=True)
       → Send email to ADMIN only
    
    2. STATUS CHANGE: pending → accepted
       → Send email to CUSTOMER
       → Send email to DRIVER (if assigned)
    
    3. STATUS CHANGE: pending → rejected
       → Send email to CUSTOMER only
    
    4. DRIVER STATUS UPDATES (picked_up/in_transit/delivered)
       → Send email to CUSTOMER
       → Send email to ADMIN
    """
    
    try:
        old_state = _pickup_previous_state.get(instance.id, {})
        old_status = old_state.get('status')
        old_driver_id = old_state.get('assigned_driver')
        
        logger.info(
            f"[POST-SAVE] Pickup #{instance.id}: "
            f"created={created}, "
            f"status_change={old_status}→{instance.status}"
        )
        
        # ============ WORKFLOW 1: NEW REQUEST ============
        if created:
            logger.info(f"[TRIGGER 1] New request created: Pickup #{instance.id}")
            _send_new_request_admin_notification(instance)
        
        # ============ WORKFLOW 2 & 3: ADMIN ACCEPTS/REJECTS ============
        elif old_status == 'pending' and instance.status == 'accepted':
            logger.info(
                f"[TRIGGER 2] Request accepted: Pickup #{instance.id}, "
                f"assigned_driver={instance.assigned_driver_id}"
            )
            _send_request_accepted_emails(instance)
        
        elif old_status == 'pending' and instance.status == 'rejected':
            logger.info(f"[TRIGGER 3] Request rejected: Pickup #{instance.id}")
            _send_request_rejected_customer_notification(instance)
        
        # ============ WORKFLOW 4: DRIVER STATUS UPDATES ============
        elif old_status != instance.status and instance.status in ['picked_up', 'in_transit', 'delivered']:
            logger.info(
                f"[TRIGGER 4] Driver status updated: Pickup #{instance.id}, "
                f"status={instance.status}"
            )
            _send_driver_status_update_emails(instance, old_status)
        
        # Clean up old state after processing
        _pickup_previous_state.pop(instance.id, None)
        
    except Exception as e:
        logger.error(
            f"Error in email notification system for pickup #{instance.id}: {str(e)}",
            exc_info=True
        )


# ============ WORKFLOW 1: NEW REQUEST → ADMIN ONLY ============

def _send_new_request_admin_notification(pickup_request):
    """
    WORKFLOW 1: New pickup request created
    
    ACTION: Send email to ADMIN ONLY
    
    Content: Request details, customer info, action needed
    """
    try:
        admin_email = settings.ADMIN_EMAIL
        
        if not admin_email:
            logger.warning("ADMIN_EMAIL not configured in settings")
            return False
        
        subject = f"🔔 New Pickup Request - #{pickup_request.tracking_number}"
        
        message = f"""
New Pickup Request Received

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CUSTOMER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {pickup_request.customer.first_name} {pickup_request.customer.last_name}
Email: {pickup_request.customer.email}
Username: {pickup_request.customer.username}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PICKUP REQUEST DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tracking Number: {pickup_request.tracking_number}
Status: {pickup_request.get_status_display()}
Created: {pickup_request.created_at.strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SENDER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {pickup_request.sender_name}
Phone: {pickup_request.sender_phone}
Address: {pickup_request.sender_address}
City: {pickup_request.sender_city}, {pickup_request.sender_state} {pickup_request.sender_zipcode}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECEIVER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {pickup_request.receiver_name}
Phone: {pickup_request.receiver_phone}
Address: {pickup_request.receiver_address}
City: {pickup_request.receiver_city}, {pickup_request.receiver_state} {pickup_request.receiver_zipcode}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PARCEL INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type: {pickup_request.get_parcel_type_display()}
Weight: {pickup_request.parcel_weight} kg
Description: {pickup_request.parcel_description or 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PICKUP TIME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Date: {pickup_request.pickup_date}
Time: {pickup_request.pickup_time or 'Not specified'}
Notes: {pickup_request.additional_notes or 'None'}

Estimated Cost: ₹{pickup_request.estimated_cost}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTION REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please review this request and assign a driver.
Access the admin panel to accept or reject this request.

---
VRL Logistics System
"""
        
        success = send_notification_email(
            subject=subject,
            message=message,
            recipient_list=[admin_email]
        )
        
        logger.info(
            f"[WORKFLOW 1 ✓] Admin notification for new request "
            f"(Pickup #{pickup_request.id}): {'SENT' if success else 'FAILED'}"
        )
        
        return success
    
    except Exception as e:
        logger.error(
            f"[WORKFLOW 1 ✗] Error sending admin notification for pickup #{pickup_request.id}: {str(e)}",
            exc_info=True
        )
        return False


# ============ WORKFLOW 2: ACCEPTED → CUSTOMER + DRIVER ============

def _send_request_accepted_emails(pickup_request):
    """
    WORKFLOW 2: Admin accepts request and assigns driver
    
    ACTIONS:
    - Send email to CUSTOMER (request accepted)
    - Send email to DRIVER (assignment details)
    """
    try:
        # Step 1: Send to CUSTOMER
        customer_email = pickup_request.customer.email
        
        if customer_email:
            success_customer = _send_customer_acceptance_notification(pickup_request)
        else:
            logger.warning(
                f"Customer {pickup_request.customer.username} has no email. "
                f"Cannot send acceptance notification for pickup #{pickup_request.id}"
            )
            success_customer = False
        
        # Step 2: Send to ASSIGNED DRIVER (if exists)
        success_driver = False
        if pickup_request.assigned_driver:
            success_driver = _send_driver_assignment_notification(pickup_request)
        else:
            logger.warning(
                f"No driver assigned for pickup #{pickup_request.id}. "
                f"Skipping driver notification."
            )
        
        logger.info(
            f"[WORKFLOW 2 ✓] Request accepted for pickup #{pickup_request.id}: "
            f"customer={success_customer}, driver={success_driver}"
        )
        
    except Exception as e:
        logger.error(
            f"[WORKFLOW 2 ✗] Error in request accepted workflow for pickup #{pickup_request.id}: {str(e)}",
            exc_info=True
        )


def _send_customer_acceptance_notification(pickup_request):
    """Send acceptance notification to customer."""
    try:
        customer_email = pickup_request.customer.email
        driver_name = pickup_request.assigned_driver.first_name if pickup_request.assigned_driver else "A"
        
        subject = f"✅ Your Pickup Request Accepted - #{pickup_request.tracking_number}"
        
        message = f"""
Your Pickup Request Has Been Accepted!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUEST ACCEPTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tracking Number: {pickup_request.tracking_number}
Status: ACCEPTED ✅

Assigned Driver: {driver_name}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PICKUP DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sender: {pickup_request.sender_name}
Receiver: {pickup_request.receiver_name}
Parcel Type: {pickup_request.get_parcel_type_display()}
Weight: {pickup_request.parcel_weight} kg

Pickup Date: {pickup_request.pickup_date}
Pickup Time: {pickup_request.pickup_time or 'Flexible'}

Estimated Cost: ₹{pickup_request.estimated_cost}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Your request has been assigned to {driver_name}
✓ The driver will arrive at the scheduled time
✓ You will receive updates as the parcel is processed

Track your shipment on our website using tracking number: {pickup_request.tracking_number}

---
VRL Logistics Team
"""
        
        success = send_notification_email(
            subject=subject,
            message=message,
            recipient_list=[customer_email]
        )
        
        logger.debug(f"Customer acceptance notification for pickup #{pickup_request.id}: {'SENT' if success else 'FAILED'}")
        return success
    
    except Exception as e:
        logger.error(f"Error sending customer acceptance notification: {str(e)}")
        return False


def _send_driver_assignment_notification(pickup_request):
    """Send assignment notification to driver."""
    try:
        driver = pickup_request.assigned_driver
        driver_email = driver.email
        
        if not driver_email:
            logger.warning(f"Driver {driver.username} has no email.")
            return False
        
        subject = f"📦 New Pickup Assignment - #{pickup_request.tracking_number}"
        
        message = f"""
You Have Been Assigned a New Pickup

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ASSIGNMENT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tracking Number: {pickup_request.tracking_number}
Status: ASSIGNED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CUSTOMER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {pickup_request.customer.first_name} {pickup_request.customer.last_name}
Phone: {pickup_request.sender_phone}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PICKUP LOCATION (SENDER)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {pickup_request.sender_name}
Address: {pickup_request.sender_address}
City: {pickup_request.sender_city}, {pickup_request.sender_state} {pickup_request.sender_zipcode}
Phone: {pickup_request.sender_phone}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DELIVERY LOCATION (RECEIVER)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {pickup_request.receiver_name}
Address: {pickup_request.receiver_address}
City: {pickup_request.receiver_city}, {pickup_request.receiver_state} {pickup_request.receiver_zipcode}
Phone: {pickup_request.receiver_phone}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PARCEL INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type: {pickup_request.get_parcel_type_display()}
Weight: {pickup_request.parcel_weight} kg
Description: {pickup_request.parcel_description or 'N/A'}
Special Notes: {pickup_request.additional_notes or 'None'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PICKUP TIME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Date: {pickup_request.pickup_date}
Time: {pickup_request.pickup_time or 'Flexible'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTION REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Accept this assignment via the mobile app
✓ Arrive at the pickup location at the scheduled time
✓ Update status as you progress through the delivery

---
VRL Logistics Driver App
"""
        
        success = send_notification_email(
            subject=subject,
            message=message,
            recipient_list=[driver_email]
        )
        
        logger.debug(f"Driver assignment notification for pickup #{pickup_request.id}: {'SENT' if success else 'FAILED'}")
        return success
    
    except Exception as e:
        logger.error(f"Error sending driver assignment notification: {str(e)}")
        return False


# ============ WORKFLOW 3: REJECTED → CUSTOMER ONLY ============

def _send_request_rejected_customer_notification(pickup_request):
    """
    WORKFLOW 3: Admin rejects request
    
    ACTION: Send email to CUSTOMER ONLY
    """
    try:
        customer_email = pickup_request.customer.email
        
        if not customer_email:
            logger.warning(f"Customer {pickup_request.customer.username} has no email.")
            return False
        
        subject = f"❌ Your Pickup Request Was Rejected - #{pickup_request.tracking_number}"
        
        message = f"""
Your Pickup Request Has Been Rejected

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUEST REJECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tracking Number: {pickup_request.tracking_number}
Status: REJECTED ❌

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PICKUP DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sender: {pickup_request.sender_name}
Receiver: {pickup_request.receiver_name}
Parcel Type: {pickup_request.get_parcel_type_display()}
Weight: {pickup_request.parcel_weight} kg

Requested Pickup Date: {pickup_request.pickup_date}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
We regret that we cannot fulfil this request at this time.

Possible reasons for rejection:
✗ Parcel type not serviceable on requested date
✗ Location outside service area
✗ Weight exceeds limits
✗ Scheduling conflict

Please create a new request or contact our support team for assistance.

Support Email: {settings.ADMIN_EMAIL}

---
VRL Logistics Team
"""
        
        success = send_notification_email(
            subject=subject,
            message=message,
            recipient_list=[customer_email]
        )
        
        logger.info(
            f"[WORKFLOW 3 ✓] Rejection notification for pickup #{pickup_request.id}: "
            f"{'SENT' if success else 'FAILED'}"
        )
        
        return success
    
    except Exception as e:
        logger.error(
            f"[WORKFLOW 3 ✗] Error sending rejection notification for pickup #{pickup_request.id}: {str(e)}",
            exc_info=True
        )
        return False


# ============ WORKFLOW 4: DRIVER STATUS UPDATES → ADMIN + CUSTOMER ============

def _send_driver_status_update_emails(pickup_request, old_status):
    """
    WORKFLOW 4: Driver updates status (picked_up/in_transit/delivered)
    
    ACTIONS:
    - Send email to ADMIN (status update alert)
    - Send email to CUSTOMER (tracking update)
    """
    try:
        # Only send for specific status changes
        if pickup_request.status not in ['picked_up', 'in_transit', 'delivered']:
            logger.debug(f"Status {pickup_request.status} not in status update list. Skipping emails.")
            return
        
        # Step 1: Send to ADMIN
        success_admin = _send_admin_status_update_notification(pickup_request, old_status)
        
        # Step 2: Send to CUSTOMER
        success_customer = _send_customer_status_update_notification(pickup_request, old_status)
        
        logger.info(
            f"[WORKFLOW 4 ✓] Status updated for pickup #{pickup_request.id}: "
            f"admin={success_admin}, customer={success_customer}"
        )
        
    except Exception as e:
        logger.error(
            f"[WORKFLOW 4 ✗] Error in driver status update workflow for pickup #{pickup_request.id}: {str(e)}",
            exc_info=True
        )


def _send_admin_status_update_notification(pickup_request, old_status):
    """Send status update to admin."""
    try:
        admin_email = settings.ADMIN_EMAIL
        driver_name = pickup_request.assigned_driver.first_name if pickup_request.assigned_driver else "Unknown"
        
        subject = f"📊 Pickup Status Update - #{pickup_request.tracking_number} [{pickup_request.get_status_display()}]"
        
        message = f"""
Pickup Status Update

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS UPDATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tracking Number: {pickup_request.tracking_number}
Previous Status: {old_status.upper()}
Current Status: {pickup_request.get_status_display().upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DRIVER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Driver: {driver_name}
Driver ID: {pickup_request.assigned_driver.username if pickup_request.assigned_driver else 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUEST DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sender: {pickup_request.sender_name} → {pickup_request.receiver_name}
Parcel Type: {pickup_request.get_parcel_type_display()}
Weight: {pickup_request.parcel_weight} kg

Pickup Started: {pickup_request.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Last Updated: {pickup_request.updated_at.strftime('%Y-%m-%d %H:%M:%S')}

Additional Notes: {pickup_request.additional_notes or 'None'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

---
VRL Logistics Admin System
"""
        
        success = send_notification_email(
            subject=subject,
            message=message,
            recipient_list=[admin_email]
        )
        
        logger.debug(f"Admin status update for pickup #{pickup_request.id}: {'SENT' if success else 'FAILED'}")
        return success
    
    except Exception as e:
        logger.error(f"Error sending admin status notification: {str(e)}")
        return False


def _send_customer_status_update_notification(pickup_request, old_status):
    """Send tracking update to customer."""
    try:
        customer_email = pickup_request.customer.email
        driver_name = pickup_request.assigned_driver.first_name if pickup_request.assigned_driver else "Driver"
        
        status_emoji = {
            'picked_up': '📦',
            'in_transit': '🚗',
            'delivered': '✅'
        }.get(pickup_request.status, '📍')
        
        subject = f"{status_emoji} Tracking Update - Your Parcel {pickup_request.get_status_display()} - #{pickup_request.tracking_number}"
        
        message = f"""
Your Parcel Tracking Update

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS UPDATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tracking Number: {pickup_request.tracking_number}
Current Status: {status_emoji} {pickup_request.get_status_display().upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DELIVERY DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
From: {pickup_request.sender_name}
To: {pickup_request.receiver_name}
Parcel: {pickup_request.get_parcel_type_display()} ({pickup_request.parcel_weight} kg)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DRIVER HANDLING YOUR PARCEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Driver Name: {driver_name}

Status Timeline:
→ Created: {pickup_request.created_at.strftime('%Y-%m-%d %H:%M:%S')}
→ Assigned: {pickup_request.created_at.strftime('%Y-%m-%d %H:%M:%S')}
→ Current: {pickup_request.updated_at.strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT'S NEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your parcel is on its way to the destination.
You will receive another update once it reaches its destination.

Track online: Visit our website with tracking number {pickup_request.tracking_number}

---
VRL Logistics Team
"""
        
        success = send_notification_email(
            subject=subject,
            message=message,
            recipient_list=[customer_email]
        )
        
        logger.debug(f"Customer status update for pickup #{pickup_request.id}: {'SENT' if success else 'FAILED'}")
        return success
    
    except Exception as e:
        logger.error(f"Error sending customer status notification: {str(e)}")
        return False
