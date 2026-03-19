"""
Django signals for WhatsApp notifications in VRL Logistics.

Automatically sends WhatsApp messages for key events:
- New pickup request created → notify customer
- Admin accepts request → notify customer  
- Driver assigned → notify driver

Uses post_save signal on PickupRequest model for reliable triggering
with proper exception handling to prevent notification failures from
breaking the main application flow.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import PickupRequest, UserProfile
from .utils import send_whatsapp_notification

# Configure logger for signals
logger = logging.getLogger(__name__)


@receiver(post_save, sender=PickupRequest)
def send_whatsapp_notifications(sender, instance, created, update_fields, **kwargs):
    """
    Signal handler to send WhatsApp notifications on pickup request events.
    
    Triggers on:
    1. New request creation → message to customer
    2. Status change to 'accepted' → message to customer
    3. Driver assignment → message to driver
    
    Args:
        sender: PickupRequest model
        instance: The PickupRequest instance
        created: Boolean indicating if instance was newly created
        update_fields: Set of fields that were updated (None on creation)
    """
    
    try:
        # Trigger 1: New pickup request created
        if created:
            _send_new_request_notification(instance)
        
        # Trigger 2: Status changed to 'accepted'
        elif update_fields and 'status' in update_fields and instance.status == 'accepted':
            _send_request_accepted_notification(instance)
        
        # Trigger 3: Driver assigned
        elif update_fields and 'assigned_driver' in update_fields and instance.assigned_driver:
            _send_driver_assigned_notification(instance)
            
    except Exception as e:
        # Log error but don't raise - prevent WhatsApp issues from breaking the app
        logger.error(
            f"Error sending WhatsApp notification for pickup #{instance.id}: {str(e)}",
            exc_info=True,
            extra={'pickup_id': instance.id, 'error_type': type(e).__name__}
        )


def _send_new_request_notification(pickup_request):
    """
    Send WhatsApp notification to customer when new pickup request is created.
    
    Args:
        pickup_request: PickupRequest instance
    """
    try:
        # Validate customer has a profile with phone number
        customer_profile = pickup_request.customer.profile
        if not customer_profile.phone_number:
            logger.warning(
                f"Customer {pickup_request.customer.username} has no phone number. "
                f"Cannot send new_request notification for pickup #{pickup_request.id}"
            )
            return
        
        # Send notification to customer
        success = send_whatsapp_notification(
            pickup_request=pickup_request,
            notification_type='new_request',
            recipient_role='customer'
        )
        
        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"New request notification for pickup #{pickup_request.id} - Customer {pickup_request.customer.username}: "
            f"{'SUCCESS' if success else 'FAILED'}"
        )
        
    except UserProfile.DoesNotExist:
        logger.warning(
            f"Customer {pickup_request.customer.username} has no profile. "
            f"Cannot send new_request notification for pickup #{pickup_request.id}"
        )


def _send_request_accepted_notification(pickup_request):
    """
    Send WhatsApp notification to customer when admin accepts request.
    
    Args:
        pickup_request: PickupRequest instance
    """
    try:
        # Validate customer has a profile with phone number
        customer_profile = pickup_request.customer.profile
        if not customer_profile.phone_number:
            logger.warning(
                f"Customer {pickup_request.customer.username} has no phone number. "
                f"Cannot send request_accepted notification for pickup #{pickup_request.id}"
            )
            return
        
        # Send notification to customer
        success = send_whatsapp_notification(
            pickup_request=pickup_request,
            notification_type='request_accepted',
            recipient_role='customer'
        )
        
        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"Request accepted notification for pickup #{pickup_request.id} - Customer {pickup_request.customer.username}: "
            f"{'SUCCESS' if success else 'FAILED'}"
        )
        
    except UserProfile.DoesNotExist:
        logger.warning(
            f"Customer {pickup_request.customer.username} has no profile. "
            f"Cannot send request_accepted notification for pickup #{pickup_request.id}"
        )


def _send_driver_assigned_notification(pickup_request):
    """
    Send WhatsApp notification to driver when assigned to a pickup request.
    
    Args:
        pickup_request: PickupRequest instance with assigned_driver set
    """
    try:
        # Validate driver exists and has a profile with phone number
        driver = pickup_request.assigned_driver
        if not driver:
            logger.warning(
                f"Pickup #{pickup_request.id} has no assigned driver. "
                f"Cannot send driver_assigned notification"
            )
            return
        
        driver_profile = driver.profile
        if not driver_profile.phone_number:
            logger.warning(
                f"Driver {driver.username} has no phone number. "
                f"Cannot send driver_assigned notification for pickup #{pickup_request.id}"
            )
            return
        
        # Send notification to driver
        success = send_whatsapp_notification(
            pickup_request=pickup_request,
            notification_type='driver_assigned',
            recipient_role='driver'
        )
        
        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"Driver assigned notification for pickup #{pickup_request.id} - Driver {driver.username}: "
            f"{'SUCCESS' if success else 'FAILED'}"
        )
        
    except UserProfile.DoesNotExist:
        logger.warning(
            f"Driver {pickup_request.assigned_driver.username} has no profile. "
            f"Cannot send driver_assigned notification for pickup #{pickup_request.id}"
        )
