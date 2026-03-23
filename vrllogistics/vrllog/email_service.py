"""
Email notification service for VRL Logistics.

PRODUCTION-GRADE email handling with comprehensive error management.

Provides centralized email sending functionality with:
- SMTP connection error handling
- Authentication error handling  
- Timeout handling with retries
- Comprehensive logging and debugging
- Gmail App Password support
- Console backend for development

Workflow Functions:
- send_new_request_notification(): Admin notification for new requests
- send_acceptance_notification(): Customer & Driver notification for acceptance
- send_rejection_notification(): Customer notification for rejection
- send_status_update_notification(): Admin & Customer for status changes
- send_driver_reassignment_notification(): Notifications for driver changes

Testing:
- test_email_connection(): Check if SMTP is properly configured
- send_test_email(recipient): Send a test email to verify system works
"""

import logging
import smtplib
import socket
from typing import List, Optional, Tuple
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
from django.template.loader import render_to_string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Get logger for this module
logger = logging.getLogger(__name__)

# Log initial configuration on module load
print("=" * 80)
print("📧 EMAIL SERVICE MODULE LOADING")
print("=" * 80)
print(f"  Email Backend: {getattr(settings, 'EMAIL_BACKEND', 'Not configured')}")
print(f"  Email Host: {getattr(settings, 'EMAIL_HOST', 'Not configured')}")
print(f"  Email Port: {getattr(settings, 'EMAIL_PORT', 'Not configured')}")
print(f"  Email Use TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not configured')}")
print(f"  Email Timeout: {getattr(settings, 'EMAIL_TIMEOUT', '10')} seconds")
print(f"  Email From: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured')}")
print(f"  Email Enabled: {getattr(settings, 'EMAIL_NOTIFICATIONS_ENABLED', False)}")
print(f"  Debug Mode: {getattr(settings, 'EMAIL_DEBUG_MODE', False)}")
print("=" * 80)


def send_notification_email(subject: str, message: str, recipient_list: List[str], html_message: Optional[str] = None, max_retries: Optional[int] = None) -> bool:
    """
    Send email notification safely with comprehensive error handling.
    
    Handles the following error types:
    - SMTP Connection Errors (gaierror, connection refused, etc.)
    - SMTP Authentication Errors (invalid credentials)
    - Timeout Errors (network delays)
    - Generic SMTP errors
    
    Args:
        subject (str): Email subject line
        message (str): Plain text email body
        recipient_list (list): List of recipient email addresses
        html_message (str, optional): HTML version of email body
        max_retries (int, optional): Number of retries on failure (overrides settings)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    
    Raises: Nothing - all errors are caught and logged
    
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
        logger.warning(
            f"🔕 EMAIL NOTIFICATIONS DISABLED. Message not sent to {recipient_list}\n"
            f"   Subject: {subject}"
        )
        return False
    
    # Validate inputs
    if not recipient_list or not subject or not message:
        logger.error(
            "❌ INVALID EMAIL PARAMETERS:\n"
            f"   Recipients: {recipient_list}\n"
            f"   Subject: {subject}\n"
            f"   Message length: {len(message) if message else 'MISSING'}"
        )
        return False
    
    # Ensure recipient_list is a list
    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]
    
    # Get max retries from parameter or settings
    if max_retries is None:
        max_retries = getattr(settings, 'EMAIL_MAX_RETRIES', 3)
    
    # Attempt to send email with retries
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        
        try:
            logger.debug(f"📧 [Attempt {attempt}/{max_retries}] Sending email to {recipient_list}")
            logger.debug(f"   Subject: {subject}")
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
                auth_user=settings.EMAIL_HOST_USER,
                auth_password=settings.EMAIL_HOST_PASSWORD,
            )
            
            logger.info(
                f"✅ EMAIL SENT SUCCESSFULLY:\n"
                f"   Recipients: {recipient_list}\n"
                f"   Subject: {subject}\n"
                f"   Attempt: {attempt}/{max_retries}"
            )
            return True
        
        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                f"❌ SMTP AUTHENTICATION ERROR (Attempt {attempt}/{max_retries}):\n"
                f"   Error: {str(e)}\n"
                f"   Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env\n"
                f"   Make sure you're using Gmail App Password, not regular password!\n"
                f"   Generate at: https://myaccount.google.com/apppasswords\n"
                f"   Recipients: {recipient_list}"
            )
            if attempt == max_retries:
                return False
        
        except smtplib.SMTPException as e:
            logger.error(
                f"❌ SMTP ERROR (Attempt {attempt}/{max_retries}):\n"
                f"   Error Type: {type(e).__name__}\n"
                f"   Message: {str(e)}\n"
                f"   Recipients: {recipient_list}"
            )
            if attempt == max_retries:
                return False
        
        except socket.gaierror as e:
            logger.error(
                f"❌ DNS/NETWORK ERROR - Cannot resolve {settings.EMAIL_HOST} (Attempt {attempt}/{max_retries}):\n"
                f"   Error: {str(e)}\n"
                f"   Check: Internet connection and EMAIL_HOST setting\n"
                f"   Recipients: {recipient_list}"
            )
            if attempt == max_retries:
                return False
        
        except socket.timeout as e:
            logger.error(
                f"❌ CONNECTION TIMEOUT (Attempt {attempt}/{max_retries}):\n"
                f"   Error: {str(e)}\n"
                f"   Timeout: {settings.EMAIL_TIMEOUT} seconds\n"
                f"   Check: Network latency or firewall blocking port {settings.EMAIL_PORT}\n"
                f"   Recipients: {recipient_list}"
            )
            if attempt == max_retries:
                return False
        
        except ConnectionRefusedError as e:
            logger.error(
                f"❌ CONNECTION REFUSED (Attempt {attempt}/{max_retries}):\n"
                f"   Error: {str(e)}\n"
                f"   Cannot connect to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}\n"
                f"   Check: Email host configuration and network connectivity\n"
                f"   Recipients: {recipient_list}"
            )
            if attempt == max_retries:
                return False
        
        except Exception as e:
            logger.error(
                f"❌ UNEXPECTED EMAIL ERROR (Attempt {attempt}/{max_retries}):\n"
                f"   Error Type: {type(e).__name__}\n"
                f"   Error: {str(e)}\n"
                f"   Recipients: {recipient_list}",
                exc_info=True
            )
            if attempt == max_retries:
                return False
    
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


# ============ TESTING & DEBUGGING FUNCTIONS ============

def test_email_connection() -> Tuple[bool, str]:
    """
    Test SMTP connection without sending email.
    
    Attempts to establish connection to configured SMTP server and verifies credentials.
    Useful for debugging email configuration issues.
    
    Returns:
        Tuple[bool, str]: (success, message)
        - success: True if connection succeeded, False otherwise
        - message: Detailed status message for logging
    
    Example:
        >>> success, msg = test_email_connection()
        >>> print(msg)
        Connection test result: ...
    """
    print("\n" + "=" * 80)
    print("🧪 TESTING EMAIL CONFIGURATION")
    print("=" * 80)
    
    # Display current configuration
    print("\n📋 CURRENT SETTINGS:")
    print(f"  Email Backend: {settings.EMAIL_BACKEND}")
    print(f"  SMTP Host: {settings.EMAIL_HOST}")
    print(f"  SMTP Port: {settings.EMAIL_PORT}")
    print(f"  Email TLS: {settings.EMAIL_USE_TLS}")
    print(f"  Email Timeout: {settings.EMAIL_TIMEOUT} sec")
    print(f"  Email Host User: {settings.EMAIL_HOST_USER}")
    print(f"  From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"  Notifications Enabled: {settings.EMAIL_NOTIFICATIONS_ENABLED}")
    print(f"  Debug Mode: {getattr(settings, 'EMAIL_DEBUG_MODE', False)}")
    
    # If using console backend for development
    if 'console' in settings.EMAIL_BACKEND.lower():
        msg = "✅ Using Console Email Backend (Development Mode) - Emails will print to console"
        print(f"\n{msg}")
        logger.info(msg)
        return True, msg
    
    # Test SMTP connection
    print("\n🔗 ATTEMPTING SMTP CONNECTION...")
    try:
        # Create SMTP connection
        server = smtplib.SMTP(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            timeout=settings.EMAIL_TIMEOUT
        )
        
        print(f"✅ Connected to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        
        # Start TLS if configured
        if settings.EMAIL_USE_TLS:
            print("🔒 Starting TLS encryption...")
            server.starttls()
            print("✅ TLS enabled")
        
        # Test authentication
        print("🔐 Testing authentication...")
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print(f"✅ Authentication successful for {settings.EMAIL_HOST_USER}")
        
        # Close connection
        server.quit()
        
        msg = "✅ EMAIL CONFIGURATION TEST PASSED - Everything looks good!"
        print(f"\n{msg}\n")
        logger.info("✅ Email connection test passed")
        return True, msg
    
    except smtplib.SMTPAuthenticationError:
        msg = (
            "❌ AUTHENTICATION FAILED\n"
            "   Possible issues:\n"
            "   1. Wrong email address (EMAIL_HOST_USER)\n"
            "   2. Wrong password - use Gmail App Password, NOT regular password!\n"
            "   3. Gmail account doesn't have App Passwords enabled\n"
            "   4. Less secure app access disabled\n"
            "\n   Fix: Generate App Password at https://myaccount.google.com/apppasswords"
        )
        print(f"\n{msg}\n")
        logger.error(msg)
        return False, msg
    
    except smtplib.SMTPException as e:
        msg = f"❌ SMTP ERROR: {type(e).__name__}: {str(e)}"
        print(f"\n{msg}\n")
        logger.error(msg)
        return False, msg
    
    except socket.gaierror as e:
        msg = (
            f"❌ DNS/NETWORK ERROR: Cannot resolve '{settings.EMAIL_HOST}'\n"
            f"   Error: {str(e)}\n"
            "   Possible issues:\n"
            "   1. Internet connection down\n"
            "   2. Wrong EMAIL_HOST value\n"
            "   3. Firewall blocking access"
        )
        print(f"\n{msg}\n")
        logger.error(msg)
        return False, msg
    
    except socket.timeout:
        msg = (
            f"❌ CONNECTION TIMEOUT: Could not connect within {settings.EMAIL_TIMEOUT} seconds\n"
            "   Possible issues:\n"
            "   1. Slow/no internet connection\n"
            "   2. Firewall blocking port {settings.EMAIL_PORT}\n"
            "   3. Network latency issue"
        )
        print(f"\n{msg}\n")
        logger.error(msg)
        return False, msg
    
    except ConnectionRefusedError as e:
        msg = (
            f"❌ CONNECTION REFUSED: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}\n"
            f"   Error: {str(e)}\n"
            "   Possible issues:\n"
            "   1. SMTP server down\n"
            "   2. Wrong port number\n"
            "   3. Correct host/port but server rejecting connections"
        )
        print(f"\n{msg}\n")
        logger.error(msg)
        return False, msg
    
    except Exception as e:
        msg = f"❌ UNEXPECTED ERROR: {type(e).__name__}: {str(e)}"
        print(f"\n{msg}\n")
        logger.error(msg, exc_info=True)
        return False, msg


def send_test_email(recipient: str) -> bool:
    """
    Send a test email to verify the email system is working.
    
    This function sends a simple test email immediately to verify:
    - SMTP connection works
    - Authentication is correct
    - Email is actually being sent
    
    Args:
        recipient (str): Email address to send test to
    
    Returns:
        bool: True if sent successfully, False otherwise
    
    Example:
        >>> # From Django shell
        >>> from vrllog.email_service import send_test_email
        >>> send_test_email('your-email@gmail.com')
        True
    """
    print("\n" + "=" * 80)
    print(f"📧 SENDING TEST EMAIL TO: {recipient}")
    print("=" * 80 + "\n")
    
    subject = "🧪 VRL Logistics - Test Email"
    message = f"""
Hello,

This is a test email from VRL Logistics email system.

If you received this, your email configuration is working correctly! ✅

═════════════════════════════════════════════════════════════
System Information:
  From: {settings.DEFAULT_FROM_EMAIL}
  Admin Email: {settings.ADMIN_EMAIL}
  Sent at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
  Backend: {settings.EMAIL_BACKEND}
═════════════════════════════════════════════════════════════

Best regards,
VRL Logistics Email System

---
Do not reply to this email. This is an automated test message.
"""
    
    html_message = f"""
<html>
<head></head>
<body style="font-family: Arial, sans-serif; color: #333;">
    <h2>🧪 VRL Logistics - Test Email</h2>
    <p>Hello,</p>
    <p>This is a <strong>test email</strong> from VRL Logistics email system.</p>
    <p style="font-size: 16px; color: #28a745;"><strong>If you received this, your email configuration is working correctly! ✅</strong></p>
    
    <hr style="border: none; border-top: 2px solid #ddd; margin: 20px 0;">
    
    <h3>System Information:</h3>
    <ul>
        <li><strong>From:</strong> {settings.DEFAULT_FROM_EMAIL}</li>
        <li><strong>Admin Email:</strong> {settings.ADMIN_EMAIL}</li>
        <li><strong>Sent at:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
        <li><strong>Backend:</strong> {settings.EMAIL_BACKEND}</li>
    </ul>
    
    <hr style="border: none; border-top: 2px solid #ddd; margin: 20px 0;">
    
    <p>Best regards,<br><strong>VRL Logistics Email System</strong></p>
    <p style="color: #999; font-size: 12px;">Do not reply to this email. This is an automated test message.</p>
</body>
</html>
"""
    
    success = send_notification_email(
        subject=subject,
        message=message,
        recipient_list=[recipient],
        html_message=html_message
    )
    
    if success:
        print(f"✅ Test email sent successfully to {recipient}")
    else:
        print(f"❌ Failed to send test email to {recipient}")
        print("   Check logs for detailed error information")
    
    print("=" * 80 + "\n")
    return success


def get_email_configuration() -> dict:
    """
    Get current email configuration as a dictionary.
    
    Returns:
        dict: Email configuration settings
    
    Example:
        >>> config = get_email_configuration()
        >>> print(config['EMAIL_HOST'])
        'smtp.gmail.com'
    """
    return {
        'EMAIL_BACKEND': settings.EMAIL_BACKEND,
        'EMAIL_HOST': settings.EMAIL_HOST,
        'EMAIL_PORT': settings.EMAIL_PORT,
        'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
        'EMAIL_USE_SSL': getattr(settings, 'EMAIL_USE_SSL', False),
        'EMAIL_TIMEOUT': settings.EMAIL_TIMEOUT,
        'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
        'ADMIN_EMAIL': settings.ADMIN_EMAIL,
        'EMAIL_NOTIFICATIONS_ENABLED': settings.EMAIL_NOTIFICATIONS_ENABLED,
        'EMAIL_DEBUG_MODE': getattr(settings, 'EMAIL_DEBUG_MODE', False),
        'EMAIL_MAX_RETRIES': getattr(settings, 'EMAIL_MAX_RETRIES', 3),
    }


# Import at end to access settings
from django.utils import timezone
