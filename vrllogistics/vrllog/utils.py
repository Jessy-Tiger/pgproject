import logging
from django.conf import settings
from django.core.cache import cache
from functools import wraps
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from io import BytesIO
import time

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

# Configure logger for WhatsApp operations
logger = logging.getLogger(__name__)


def handle_whatsapp_errors(func):
    """
    Decorator to handle WhatsApp message sending errors gracefully.
    Prevents WhatsApp failures from breaking the request/response cycle.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {type(e).__name__}: {str(e)}")
            return False
    return wrapper


@handle_whatsapp_errors
def send_whatsapp_message(phone_number, message, message_type='notification'):
    """
    Send WhatsApp message using Twilio API.
    
    Args:
        phone_number (str): Recipient phone number in international format (+91XXXXXXXXXX)
        message (str): Message text to send
        message_type (str): Type of message (notification, confirmation, alert, etc.)
    
    Returns:
        str: Message SID if successful, None if failed
    
    Example:
        send_whatsapp_message(
            phone_number='+919876543210',
            message='Your pickup request has been created!',
            message_type='new_request'
        )
    """
    
    # Check if WhatsApp notifications are enabled
    if not settings.WHATSAPP_NOTIFICATIONS_ENABLED:
        logger.info(f"WhatsApp notifications disabled. Message not sent to {phone_number}")
        return None
    
    # Validate inputs
    if not phone_number or not message:
        logger.warning("Invalid WhatsApp message parameters (phone_number or message missing)")
        return None
    
    # Ensure phone number has whatsapp: prefix
    if not phone_number.startswith('whatsapp:'):
        phone_number = f'whatsapp:{phone_number}'
    
    # Check if Twilio is available
    if not TWILIO_AVAILABLE:
        logger.error("Twilio library not installed. Install with: pip install twilio")
        return None
    
    try:
        # Initialize Twilio client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Send message with retry logic
        message_obj = None
        for attempt in range(settings.WHATSAPP_RETRY_ATTEMPTS):
            try:
                message_obj = client.messages.create(
                    body=message,
                    from_=settings.TWILIO_WHATSAPP_NUMBER,
                    to=phone_number,
                )
                break  # Success, exit retry loop
            except Exception as retry_error:
                if attempt < settings.WHATSAPP_RETRY_ATTEMPTS - 1:
                    wait_time = settings.WHATSAPP_RETRY_DELAY * (attempt + 1)
                    logger.warning(f"WhatsApp send failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(retry_error)}")
                    time.sleep(wait_time)
                else:
                    raise retry_error
        
        if message_obj and message_obj.sid:
            logger.info(f"WhatsApp message sent successfully: {message_obj.sid} to {phone_number} (type: {message_type})")
            return message_obj.sid
        else:
            logger.error(f"WhatsApp message failed: No message SID returned for {phone_number}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message to {phone_number}: {type(e).__name__}: {str(e)}")
        return None


def format_whatsapp_message(template_name, context=None):
    """
    Format WhatsApp message from template.
    
    Args:
        template_name (str): Template name (e.g., 'new_request', 'confirmed', etc.)
        context (dict): Context variables for message formatting
    
    Returns:
        str: Formatted message text
    
    Example:
        message = format_whatsapp_message(
            'new_request',
            {'tracking_number': 'TRK123', 'sender_name': 'John'}
        )
    """
    
    if context is None:
        context = {}
    
    # Define message templates
    templates = {
        'new_request': (
            "🚚 *VRL Logistics*\n\n"
            "New Pickup Request Created\n\n"
            "📍 Tracking Number: {tracking_number}\n"
            "👤 Sender: {sender_name}\n"
            "📦 Receiver: {receiver_name}\n"
            "📮 Pickup From: {sender_address}\n\n"
            "Our logistics team will process your request soon. "
            "You'll receive an update shortly!"
        ),
        'request_accepted': (
            "✅ *VRL Logistics - Request Accepted*\n\n"
            "Good News! Your pickup request has been accepted.\n\n"
            "📍 Tracking Number: {tracking_number}\n"
            "📅 Pickup Date/Time: {pickup_date} at {pickup_time}\n"
            "📮 Pickup Address: {pickup_address}\n\n"
            "A driver will be assigned shortly. Stay tuned!"
        ),
        'request_rejected': (
            "❌ *VRL Logistics - Request Update*\n\n"
            "We're unable to process your pickup request.\n\n"
            "📍 Tracking Number: {tracking_number}\n"
            "Reason: {reason}\n\n"
            "Please contact our support team for assistance."
        ),
        'driver_assigned': (
            "👨‍💼 *VRL Logistics - Driver Assigned*\n\n"
            "A driver has been assigned to your request!\n\n"
            "📍 Tracking Number: {tracking_number}\n"
            "🚗 Driver: {driver_name}\n"
            "📱 Driver Contact: {driver_phone}\n"
            "📅 Pickup Time: {pickup_time}\n\n"
            "Confirm your presence at the pickup location."
        ),
        'assignment_accepted': (
            "✅ *VRL Logistics - Assignment Confirmed*\n\n"
            "Thank you for accepting this assignment!\n\n"
            "📍 Tracking Number: {tracking_number}\n"
            "👤 Customer: {customer_name}\n"
            "📅 Pickup Date: {pickup_date}\n"
            "⏰ Time: {pickup_time}\n\n"
            "Please proceed to the pickup location as scheduled."
        ),
        'assignment_accepted_admin': (
            "✅ *VRL Logistics - Driver Assignment Confirmed*\n\n"
            "Great! Driver has accepted the pickup assignment.\n\n"
            "📍 Tracking Number: {tracking_number}\n"
            "🚗 Driver: {driver_name}\n"
            "👤 Customer: {customer_name}\n"
            "📅 Pickup Date: {pickup_date} at {pickup_time}\n"
            "📮 Location: {pickup_address}\n\n"
            "Pickup is now ready for execution."
        ),
        'assignment_reassigned': (
            "⚠️ *VRL Logistics - Assignment Updated*\n\n"
            "Your pickup has been reassigned to another driver.\n\n"
            "📍 Tracking Number: {tracking_number}\n"
            "Reason: {reason}\n\n"
            "You'll receive a confirmation from the new driver shortly."
        ),
        'assignment_waiting': (
            "⏳ *VRL Logistics - Finding Driver*\n\n"
            "We're actively finding a driver for your request.\n\n"
            "📍 Tracking Number: {tracking_number}\n"
            "Status: Waiting for driver confirmation\n\n"
            "This may take a few more minutes due to high demand. "
            "Thank you for your patience!"
        ),
    }
    
    # Get template
    template = templates.get(template_name)
    if not template:
        logger.warning(f"WhatsApp template not found: {template_name}")
        return f"Update for Request: {context.get('tracking_number', 'Unknown')}"
    
    # Format message with context
    try:
        # Use safe formatting to avoid KeyError
        message = template.format(**{key: str(value) if value is not None else 'N/A' 
                                     for key, value in context.items()})
        return message
    except KeyError as e:
        logger.error(f"Missing context variable {e} for template {template_name}")
        # Return template with available variables only
        available_context = {k: v for k, v in context.items() if '{' + k + '}' in template}
        return template.format(**available_context) if available_context else template


def send_whatsapp_notification(pickup_request, notification_type, recipient_role, reason=None):
    """
    Send WhatsApp notification based on event type and recipient role.
    
    This is the main dispatcher function for all WhatsApp notifications in the system.
    
    Args:
        pickup_request (PickupRequest): The pickup request object
        notification_type (str): Type of notification:
            - 'new_request': New pickup request created (to admin)
            - 'request_accepted': Admin accepted the request (to customer)
            - 'request_rejected': Admin rejected the request (to customer)
            - 'driver_assigned': Driver assigned to request (to driver)
            - 'assignment_accepted': Driver accepted assignment (to driver)
            - 'assignment_reassigned': Driver reassigned after rejection (to customer)
            - 'assignment_waiting': No drivers available, waiting (to customer)
        recipient_role (str): Role of recipient ('customer', 'admin', or 'driver')
        reason (str, optional): Additional reason/message (for rejections, reassignments)
    
    Returns:
        bool: True if message sent successfully, False otherwise
    
    Example:
        send_whatsapp_notification(
            pickup_request=pickup_obj,
            notification_type='driver_assigned',
            recipient_role='driver'
        )
    """
    
    # Validate inputs
    if not pickup_request or not notification_type or not recipient_role:
        logger.warning("Invalid WhatsApp notification parameters")
        return False
    
    # Get notification configuration
    notification_config = _get_whatsapp_config(
        pickup_request, notification_type, recipient_role, reason
    )
    
    if not notification_config:
        logger.warning(f"No WhatsApp config found for {notification_type} -> {recipient_role}")
        return False
    
    phone_number = notification_config.get('phone_number')
    template_name = notification_config.get('template_name')
    context = notification_config.get('context', {})
    
    if not phone_number:
        logger.warning(f"No phone number available for {recipient_role} in {notification_type}")
        return False
    
    # Format message
    message = format_whatsapp_message(template_name, context)
    
    # Send message
    message_sid = send_whatsapp_message(
        phone_number=phone_number,
        message=message,
        message_type=notification_type
    )
    
    return bool(message_sid)


def _get_whatsapp_config(pickup_request, notification_type, recipient_role, reason=None):
    """
    Get WhatsApp notification configuration for a given event type.
    
    Args:
        pickup_request: PickupRequest object
        notification_type: Type of notification
        recipient_role: Role of recipient
        reason: Optional reason for rejection/reassignment
    
    Returns:
        dict: Configuration with phone_number, template_name, context
    """
    
    config = {}
    
    # Get admin phone number from settings
    admin_phone = getattr(settings, 'ADMIN_PHONE_NUMBER', '+919999999999')
    
    if notification_type == 'new_request' and recipient_role == 'admin':
        # Admin receives notification about new request
        config = {
            'phone_number': admin_phone,
            'template_name': 'new_request',
            'context': {
                'tracking_number': pickup_request.tracking_number,
                'sender_name': pickup_request.sender_name,
                'receiver_name': pickup_request.receiver_name,
                'sender_address': f"{pickup_request.sender_address}, {pickup_request.sender_city}",
            }
        }
    
    elif notification_type == 'request_accepted' and recipient_role == 'customer':
        # Customer receives notification that request was accepted
        # Use sender_phone from pickup request (customer's phone)
        customer_phone = pickup_request.sender_phone if pickup_request.sender_phone else None
        if not customer_phone or customer_phone.strip() == '':
            logger.warning(f"No phone number available for customer in pickup {pickup_request.id}")
            customer_phone = None
        
        if customer_phone:
            # Ensure phone has country code
            if not customer_phone.startswith('+'):
                customer_phone = '+91' + customer_phone.lstrip('0')
        
        config = {
            'phone_number': customer_phone,
            'template_name': 'request_accepted',
            'context': {
                'tracking_number': pickup_request.tracking_number,
                'pickup_date': pickup_request.pickup_date.strftime('%d-%m-%Y') if pickup_request.pickup_date else 'TBD',
                'pickup_time': pickup_request.pickup_time,
                'pickup_address': f"{pickup_request.sender_address}, {pickup_request.sender_city}",
            }
        }
    
    elif notification_type == 'request_rejected' and recipient_role == 'customer':
        # Customer receives notification that request was rejected
        # Use sender_phone from pickup request
        customer_phone = pickup_request.sender_phone if pickup_request.sender_phone else None
        if customer_phone and not customer_phone.startswith('+'):
            customer_phone = '+91' + customer_phone.lstrip('0')
        
        config = {
            'phone_number': customer_phone,
            'template_name': 'request_rejected',
            'context': {
                'tracking_number': pickup_request.tracking_number,
                'reason': reason or 'Not specified',
            }
        }
    
    elif notification_type == 'driver_assigned' and recipient_role == 'driver':
        # Driver receives notification about assignment
        # Use driver's profile phone number
        driver_profile = getattr(pickup_request.assigned_driver, 'profile', None)
        driver_phone = driver_profile.phone_number if driver_profile and driver_profile.phone_number else None
        
        if driver_phone and not driver_phone.startswith('+'):
            driver_phone = '+91' + driver_phone.lstrip('0')
        
        config = {
            'phone_number': driver_phone,
            'template_name': 'driver_assigned',
            'context': {
                'tracking_number': pickup_request.tracking_number,
                'customer_name': pickup_request.customer.first_name or pickup_request.customer.username,
                'driver_name': pickup_request.assigned_driver.first_name or pickup_request.assigned_driver.username,
                'driver_phone': driver_phone,
                'pickup_time': pickup_request.pickup_time,
            }
        }
    
    elif notification_type == 'assignment_accepted' and recipient_role == 'driver':
        # Driver receives confirmation of accepted assignment
        # Use driver's profile phone number
        driver_profile = getattr(pickup_request.assigned_driver, 'profile', None)
        driver_phone = driver_profile.phone_number if driver_profile and driver_profile.phone_number else None
        
        if driver_phone and not driver_phone.startswith('+'):
            driver_phone = '+91' + driver_phone.lstrip('0')
        
        config = {
            'phone_number': driver_phone,
            'template_name': 'assignment_accepted',
            'context': {
                'tracking_number': pickup_request.tracking_number,
                'customer_name': pickup_request.customer.first_name or pickup_request.customer.username,
                'pickup_date': pickup_request.pickup_date.strftime('%d-%m-%Y') if pickup_request.pickup_date else 'TBD',
                'pickup_time': pickup_request.pickup_time,
            }
        }
    
    elif notification_type == 'assignment_accepted' and recipient_role == 'admin':
        # Admin receives confirmation that driver accepted assignment
        config = {
            'phone_number': admin_phone,
            'template_name': 'assignment_accepted_admin',
            'context': {
                'tracking_number': pickup_request.tracking_number,
                'driver_name': pickup_request.assigned_driver.first_name or pickup_request.assigned_driver.username,
                'customer_name': pickup_request.customer.first_name or pickup_request.customer.username,
                'pickup_date': pickup_request.pickup_date.strftime('%d-%m-%Y') if pickup_request.pickup_date else 'TBD',
                'pickup_time': pickup_request.pickup_time,
                'pickup_address': f"{pickup_request.sender_address}, {pickup_request.sender_city}",
            }
        }
    
    elif notification_type == 'assignment_reassigned' and recipient_role == 'customer':
        # Customer receives notification about reassignment
        # Use sender_phone from pickup request
        customer_phone = pickup_request.sender_phone if pickup_request.sender_phone else None
        if customer_phone and not customer_phone.startswith('+'):
            customer_phone = '+91' + customer_phone.lstrip('0')
        
        config = {
            'phone_number': customer_phone,
            'template_name': 'assignment_reassigned',
            'context': {
                'tracking_number': pickup_request.tracking_number,
                'reason': reason or 'Driver reassigned',
            }
        }
    
    elif notification_type == 'assignment_waiting' and recipient_role == 'customer':
        # Customer receives notification that system is waiting for driver
        # Use sender_phone from pickup request
        customer_phone = pickup_request.sender_phone if pickup_request.sender_phone else None
        if customer_phone and not customer_phone.startswith('+'):
            customer_phone = '+91' + customer_phone.lstrip('0')
        
        config = {
            'phone_number': customer_phone,
            'template_name': 'assignment_waiting',
            'context': {
                'tracking_number': pickup_request.tracking_number,
            }
        }
    
    return config


def generate_invoice_pdf(invoice, pickup_request):
    """
    Generate invoice PDF using ReportLab.
    
    Args:
        invoice: Invoice object
        pickup_request: PickupRequest object (for details)
    
    Returns:
        BytesIO object containing the PDF
    """
    buffer = BytesIO()
    
    # Create PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=0.5*inch, leftMargin=0.5*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=10,
    )
    
    # Add title
    elements.append(Paragraph("INVOICE", title_style))
    
    # Invoice details
    invoice_details = f"""
    <b>Invoice Number:</b> {invoice.invoice_number}<br/>
    <b>Date:</b> {invoice.issued_date.strftime('%Y-%m-%d')}<br/>
    <b>Tracking Number:</b> {pickup_request.tracking_number}<br/>
    """
    elements.append(Paragraph(invoice_details, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Customer details
    elements.append(Paragraph("Customer Details", heading_style))
    customer_details = f"""
    {pickup_request.customer.first_name} {pickup_request.customer.last_name}<br/>
    Email: {pickup_request.customer.email}<br/>
    """
    elements.append(Paragraph(customer_details, styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Sender and Receiver details
    elements.append(Paragraph("Shipment Details", heading_style))
    shipment_details = f"""
    <b>From:</b> {pickup_request.sender_name}, {pickup_request.sender_address}, {pickup_request.sender_city}, {pickup_request.sender_state} {pickup_request.sender_zipcode}<br/>
    <b>To:</b> {pickup_request.receiver_name}, {pickup_request.receiver_address}, {pickup_request.receiver_city}, {pickup_request.receiver_state} {pickup_request.receiver_zipcode}<br/>
    <b>Parcel Type:</b> {pickup_request.get_parcel_type_display()}<br/>
    <b>Weight:</b> {pickup_request.parcel_weight} kg<br/>
    """
    elements.append(Paragraph(shipment_details, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Charges table
    elements.append(Paragraph("Charges", heading_style))
    
    data = [
        ['Description', 'Amount'],
        ['Base Charge', f'₹ {invoice.base_charge:.2f}'],
        ['Weight Charge', f'₹ {invoice.weight_charge:.2f}'],
        ['Tax (GST)', f'₹ {invoice.tax:.2f}'],
        ['TOTAL', f'₹ {invoice.total_amount:.2f}'],
    ]
    
    table = Table(data, colWidths=[4*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Terms
    terms = """
    <b>Terms & Conditions:</b><br/>
    1. This invoice is for the pickup and delivery service rendered.<br/>
    2. Payment should be made within 7 days of invoice date.<br/>
    3. For any queries, please contact our customer support.<br/>
    """
    elements.append(Paragraph(terms, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    # Reset buffer position
    buffer.seek(0)
    return buffer
