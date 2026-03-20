"""
Email notification service for VRL Logistics.

Provides centralized email sending functionality with error handling
for order notifications, status updates, and alerts.

Workflow Functions:
- send_new_request_notification(): Admin notification for new requests
- send_acceptance_notification(): Customer & Driver notification for acceptance
- send_rejection_notification(): Customer notification for rejection
- send_status_update_notification(): Admin & Customer for status changes
- send_driver_reassignment_notification(): Notifications for driver changes
"""

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_notification_email(subject, message, recipient_list, html_message=None):
    """
    Send email notification safely with error handling.
    
    Args:
        subject (str): Email subject line
        message (str): Plain text email body
        recipient_list (list): List of recipient email addresses
        html_message (str, optional): HTML version of email body
    
    Returns:
        bool: True if email sent successfully, False otherwise
    
    Example:
        send_notification_email(
            subject="Pickup Request Created",
            message="Your pickup request has been created.",
            recipient_list=["customer@example.com"],
            html_message="<p>Your pickup request has been created.</p>"
        )
    """
    
    # Check if email notifications are enabled
    if not settings.EMAIL_NOTIFICATIONS_ENABLED:
        logger.info(f"Email notifications disabled. Message not sent to {recipient_list}")
        return False
    
    # Validate inputs
    if not recipient_list or not subject or not message:
        logger.warning("Invalid email parameters (recipients, subject, or message missing)")
        return False
    
    # Ensure recipient_list is a list
    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email sent successfully to {recipient_list}: {subject}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {type(e).__name__}: {str(e)}")
        return False


def send_admin_notification(subject, message, html_message=None):
    """
    Send notification email to admin.
    
    Args:
        subject (str): Email subject
        message (str): Email body text
        html_message (str, optional): HTML email body
    
    Returns:
        bool: Success status
    """
    return send_notification_email(
        subject=subject,
        message=message,
        recipient_list=[settings.ADMIN_EMAIL],
        html_message=html_message
    )


# ============ WORKFLOW SPECIFIC FUNCTIONS ============

def send_new_request_notification(customer_email, tracking_number, sender_name):
    """
    WORKFLOW 1: Send admin notification for new pickup request.
    
    Called when: PickupRequest.created = True
    Recipient: ADMIN ONLY
    
    Args:
        customer_email (str): Customer email address
        tracking_number (str): Tracking number for the request
        sender_name (str): Name of sender
    
    Returns:
        bool: Success status
    """
    subject = f"Pickup Request Created - Tracking #{tracking_number}"
    message = (
        f"Dear Customer,\n\n"
        f"Your pickup request has been created successfully.\n"
        f"Tracking Number: {tracking_number}\n"
        f"Sender: {sender_name}\n\n"
        f"You will receive further updates as your request is processed.\n"
        f"Thank you for using VRL Logistics.\n\n"
        f"Best regards,\nVRL Logistics Team"
    )
    
    return send_notification_email(
        subject=subject,
        message=message,
        recipient_list=[customer_email]
    )


def send_request_accepted_notification(customer_email, tracking_number, driver_name=None):
    """
    WORKFLOW 2A: Send email to customer when request is accepted.
    
    Called when: status changes to 'accepted' or 'assigned'
    Recipient: CUSTOMER ONLY
    
    Args:
        customer_email (str): Customer email address
        tracking_number (str): Tracking number
        driver_name (str, optional): Name of assigned driver
    
    Returns:
        bool: Success status
    """
    subject = f"Your Pickup Request Accepted - Tracking #{tracking_number}"
    driver_info = f"Your assigned driver is: {driver_name}\n" if driver_name else ""
    message = (
        f"Dear Customer,\n\n"
        f"Your pickup request has been accepted and assigned.\n"
        f"Tracking Number: {tracking_number}\n"
        f"{driver_info}\n"
        f"A driver will be arriving soon to pick up your parcel.\n"
        f"Thank you for using VRL Logistics.\n\n"
        f"Best regards,\nVRL Logistics Team"
    )
    
    return send_notification_email(
        subject=subject,
        message=message,
        recipient_list=[customer_email]
    )


def send_driver_assignment_notification(driver_email, tracking_number, sender_name, pickup_date, time_window):
    """
    WORKFLOW 2B: Send email to driver when assigned a pickup.
    
    Called when: driver is assigned to request
    Recipient: DRIVER ONLY
    
    Args:
        driver_email (str): Driver email address
        tracking_number (str): Tracking number
        sender_name (str): Sender name
        pickup_date (str): Date of pickup
        time_window (str): Time window for pickup
    
    Returns:
        bool: Success status
    """
    subject = f"New Pickup Assignment - Tracking #{tracking_number}"
    message = (
        f"Dear Driver,\n\n"
        f"You have been assigned a new pickup request.\n\n"
        f"Tracking Number: {tracking_number}\n"
        f"Sender Name: {sender_name}\n"
        f"Pickup Date: {pickup_date}\n"
        f"Time Window: {time_window}\n\n"
        f"Please accept or reject this assignment in your dashboard.\n\n"
        f"Best regards,\nVRL Logistics Team"
    )
    
    return send_notification_email(
        subject=subject,
        message=message,
        recipient_list=[driver_email]
    )


def send_request_rejection_notification(customer_email, tracking_number):
    """
    WORKFLOW 3: Send email to customer when request is rejected.
    
    Called when: status changes from 'pending' to 'rejected'
    Recipient: CUSTOMER ONLY
    
    Args:
        customer_email (str): Customer email address
        tracking_number (str): Tracking number
    
    Returns:
        bool: Success status
    """
    subject = f"Pickup Request Rejected - Tracking #{tracking_number}"
    message = (
        f"Dear Customer,\n\n"
        f"Unfortunately, your pickup request has been rejected.\n"
        f"Tracking Number: {tracking_number}\n\n"
        f"Possible reasons:\n"
        f"- Parcel type not serviceable on requested date\n"
        f"- Location outside service area\n"
        f"- Weight exceeds limits\n"
        f"- Scheduling conflict\n\n"
        f"Please create a new request or contact support.\n"
        f"Support Email: {settings.ADMIN_EMAIL}\n\n"
        f"Best regards,\nVRL Logistics Team"
    )
    
    return send_notification_email(
        subject=subject,
        message=message,
        recipient_list=[customer_email]
    )


def send_driver_status_update_notification(admin_email, tracking_number, driver_name, status, notes=None):
    """
    WORKFLOW 4A: Send email to admin on driver status update.
    
    Called when: status changes to 'picked_up', 'in_transit', 'delivered'
    Recipient: ADMIN ONLY
    
    Args:
        admin_email (str): Admin email address
        tracking_number (str): Tracking number
        driver_name (str): Driver name
        status (str): Updated status
        notes (str, optional): Additional notes
    
    Returns:
        bool: Success status
    """
    subject = f"Pickup Status Update - Tracking #{tracking_number}"
    notes_info = f"\nNotes: {notes}" if notes else ""
    message = (
        f"Dear Admin,\n\n"
        f"Pickup status has been updated.\n\n"
        f"Tracking Number: {tracking_number}\n"
        f"Driver: {driver_name}\n"
        f"Status: {status}{notes_info}\n\n"
        f"Please review this update in your dashboard.\n\n"
        f"Best regards,\nVRL Logistics Team"
    )
    
    return send_notification_email(
        subject=subject,
        message=message,
        recipient_list=[admin_email]
    )


def send_customer_tracking_update_notification(customer_email, tracking_number, status, driver_name=None):
    """
    WORKFLOW 4B: Send tracking update email to customer.
    
    Called when: status changes to 'picked_up', 'in_transit', 'delivered'
    Recipient: CUSTOMER ONLY
    
    Args:
        customer_email (str): Customer email address
        tracking_number (str): Tracking number
        status (str): Updated status
        driver_name (str, optional): Driver handling the parcel
    
    Returns:
        bool: Success status
    """
    status_emoji = {
        'picked_up': '📦',
        'in_transit': '🚗',
        'delivered': '✅'
    }.get(status, '📍')
    
    subject = f"{status_emoji} Your Parcel {status.replace('_', ' ').title()} - #{tracking_number}"
    message = (
        f"Dear Customer,\n\n"
        f"Tracking Update: {status.replace('_', ' ').upper()}\n\n"
        f"Tracking Number: {tracking_number}\n"
        f"Status: {status.replace('_', ' ').upper()}\n"
        f"{f'Driver: {driver_name}' if driver_name else ''}\n\n"
        f"Your parcel is on its way. You will receive another update once it reaches its destination.\n\n"
        f"Track online: Visit our website with tracking number {tracking_number}\n\n"
        f"Best regards,\nVRL Logistics Team"
    )
    
    return send_notification_email(
        subject=subject,
        message=message,
        recipient_list=[customer_email]
    )


# ============ LEGACY FUNCTIONS (kept for backward compatibility) ============

def send_pickup_request_confirmation(customer_email, tracking_number, sender_name):
    """
    DEPRECATED: Use send_new_request_notification instead.
    Send confirmation email when customer creates a pickup request.
    
    Args:
        customer_email (str): Customer email address
        tracking_number (str): Tracking number for the request
        sender_name (str): Name of sender
    
    Returns:
        bool: Success status
    """
    return send_new_request_notification(customer_email, tracking_number, sender_name)
