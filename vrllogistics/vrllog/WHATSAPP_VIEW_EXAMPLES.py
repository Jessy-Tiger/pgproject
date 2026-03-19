"""
WhatsApp Integration Examples for Views and Admin
==================================================

EXAMPLE 1: Create Pickup Request View
======================================

This shows how the WhatsApp notification is automatically triggered when
a pickup request is created. No additional code is needed - just inherit
from the models that have signal handlers.
"""

# vrllog/views.py - Example create_pickup_request view

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PickupRequest, UserProfile
from .forms import PickupRequestForm


@login_required(login_url='login')
def create_pickup_request(request):
    """
    Create a new pickup request.
    
    WhatsApp notification is AUTOMATICALLY sent to the customer
    via Django signal (signals.py -> _send_new_request_notification)
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'customer':
        messages.error(request, 'Only customers can create pickup requests.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PickupRequestForm(request.POST)
        if form.is_valid():
            # Save the form (this triggers the post_save signal)
            pickup = form.save(commit=False)
            pickup.customer = request.user
            pickup.save()
            # ✓ SIGNAL AUTOMATICALLY SENDS 'new_request' notification to customer
            
            messages.success(
                request,
                f'Pickup request created successfully! Tracking: {pickup.tracking_number}'
            )
            return redirect('view_pickup_requests')
    else:
        form = PickupRequestForm()
    
    context = {'form': form}
    return render(request, 'customer/create_pickup.html', context)


# ============================================================
# EXAMPLE 2: Admin Accepts Request
# ============================================================

@login_required(login_url='login')
def process_request(request, pickup_id):
    """
    Admin processes (accepts/rejects) a pickup request.
    
    When status changes to 'accepted':
    - WhatsApp notification sent to customer via signal
    - _send_request_accepted_notification() is called automatically
    """
    pickup = get_object_or_404(PickupRequest, id=pickup_id)
    
    # Verify user is admin
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, 'Only admins can process requests.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')  # 'accept' or 'reject'
        
        if action == 'accept':
            pickup.status = 'accepted'
            pickup.save()
            # ✓ SIGNAL AUTOMATICALLY SENDS 'request_accepted' notification to customer
            messages.success(request, 'Request accepted! Notification sent to customer.')
        
        elif action == 'reject':
            reason = request.POST.get('reason', 'Unable to fulfill request')
            pickup.status = 'rejected'
            pickup.save()
            # Note: You could send 'request_rejected' notification here if needed
            # send_whatsapp_notification(pickup, 'request_rejected', 'customer', reason)
            messages.success(request, 'Request rejected. Notification sent to customer.')
        
        return redirect('view_all_requests')
    
    context = {'pickup': pickup}
    return render(request, 'admin/process_request.html', context)


# ============================================================
# EXAMPLE 3: Assign Driver to Request
# ============================================================

@login_required(login_url='login')
def assign_driver(request, pickup_id):
    """
    Admin assigns a driver to a pickup request.
    
    When assigned_driver field is updated:
    - WhatsApp notification sent to driver via signal
    - _send_driver_assigned_notification() is called automatically
    """
    pickup = get_object_or_404(PickupRequest, id=pickup_id)
    
    # Verify user is admin
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if user_profile.role != 'admin':
        messages.error(request, 'Only admins can assign drivers.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        driver_id = request.POST.get('driver_id')
        
        try:
            from django.contrib.auth.models import User
            driver = User.objects.get(id=driver_id)
            
            # Check driver profile
            driver_profile = driver.profile
            if driver_profile.role != 'driver' or not driver_profile.is_active_user:
                messages.error(request, 'Selected user is not an active driver.')
                return redirect('assign_driver', pickup_id=pickup_id)
            
            # Assign driver
            pickup.assigned_driver = driver
            pickup.status = 'assigned'
            pickup.save()
            # ✓ SIGNAL AUTOMATICALLY SENDS 'driver_assigned' notification to driver
            
            messages.success(
                request,
                f'Driver {driver.first_name} assigned successfully! Notification sent.'
            )
            return redirect('view_all_requests')
        
        except User.DoesNotExist:
            messages.error(request, 'Driver not found.')
            return redirect('assign_driver', pickup_id=pickup_id)
    
    # GET - show form with available drivers
    from django.db.models import Q, Count
    available_drivers = User.objects.filter(
        profile__role='driver',
        profile__is_active_user=True
    ).annotate(
        pending_count=Count('assigned_pickups', 
                          filter=Q(assigned_pickups__status='pending_driver_acceptance'))
    ).order_by('pending_count')
    
    context = {
        'pickup': pickup,
        'available_drivers': available_drivers,
    }
    return render(request, 'admin/assign_driver.html', context)


# ============================================================
# EXAMPLE 4: Manual Notification Trigger (Optional)
# ============================================================

"""
If you ever need to manually send a notification outside of the
automatic signal handlers, use send_whatsapp_notification() directly:
"""

from vrllog.utils import send_whatsapp_notification
import logging

logger = logging.getLogger(__name__)


def manually_send_notification(request, pickup_id, notification_type):
    """
    Example of manually sending a WhatsApp notification.
    
    Not recommended - signals handle this automatically.
    Only use if you have special requirements.
    """
    pickup = get_object_or_404(PickupRequest, id=pickup_id)
    
    # Determine recipient based on notification type
    recipient_mapping = {
        'new_request': 'customer',
        'request_accepted': 'customer',
        'request_rejected': 'customer',
        'driver_assigned': 'driver',
        'assignment_accepted': 'admin',
        'assignment_waiting': 'customer',
    }
    
    recipient_role = recipient_mapping.get(notification_type)
    if not recipient_role:
        messages.error(request, 'Invalid notification type.')
        return redirect('view_all_requests')
    
    try:
        success = send_whatsapp_notification(
            pickup_request=pickup,
            notification_type=notification_type,
            recipient_role=recipient_role
        )
        
        if success:
            messages.success(request, 'Notification sent successfully.')
            logger.info(f"Manual WhatsApp notification sent: {notification_type} for pickup #{pickup.id}")
        else:
            messages.warning(request, 'Failed to send notification. Check logs.')
            logger.warning(f"Failed to send WhatsApp notification: {notification_type} for pickup #{pickup.id}")
    
    except Exception as e:
        messages.error(request, f'Error sending notification: {str(e)}')
        logger.error(f"Error in manual notification for pickup #{pickup.id}: {str(e)}", exc_info=True)
    
    return redirect('view_all_requests')


# ============================================================
# EXAMPLE 5: Admin Interface Integration
# ============================================================

"""
If you're using Django Admin, you can also add custom actions
that trigger notifications. Example:
"""

from django.contrib import admin
from .models import PickupRequest


class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'assigned_driver', 'tracking_number']
    list_filter = ['status', 'created_at']
    search_fields = ['tracking_number', 'customer__username', 'sender_name']
    
    actions = ['accept_request', 'reject_request']
    
    def accept_request(self, request, queryset):
        """
        Admin action to accept multiple requests.
        Notifications sent via signal.
        """
        count = 0
        for pickup in queryset:
            if pickup.status == 'pending':
                pickup.status = 'accepted'
                pickup.save()  # ✓ Signal sends notification
                count += 1
        
        self.message_user(
            request,
            f'{count} requests accepted. Notifications sent to customers.'
        )
    
    accept_request.short_description = "Accept selected requests"
    
    def reject_request(self, request, queryset):
        """
        Admin action to reject multiple requests.
        Notifications sent via signal.
        """
        count = 0
        for pickup in queryset:
            if pickup.status == 'pending':
                pickup.status = 'rejected'
                pickup.save()
                # Note: Could also send 'request_rejected' notification manually if needed
                count += 1
        
        self.message_user(
            request,
            f'{count} requests rejected. Notifications sent to customers.'
        )
    
    reject_request.short_description = "Reject selected requests"


# ============================================================
# EXAMPLE 6: Testing in Django Shell
# ============================================================

"""
Test WhatsApp notifications using Django shell:

    python manage.py shell

    from django.contrib.auth.models import User
    from vrllog.models import PickupRequest, UserProfile
    from datetime import date, time
    
    # Get or create test users
    customer = User.objects.get(username='testcustomer')
    driver = User.objects.get(username='testdriver')
    
    # Ensure they have profiles with phone numbers
    customer.profile.phone_number = '+919876543210'
    customer.profile.save()
    
    driver.profile.phone_number = '+918765432109'
    driver.profile.save()
    
    # Create pickup - triggers 'new_request' notification
    pickup = PickupRequest.objects.create(
        customer=customer,
        sender_name="Test Sender",
        sender_phone="+919876543210",
        sender_address="123 Test St",
        sender_city="Mumbai",
        sender_state="Maharashtra",
        sender_zipcode="400001",
        receiver_name="Test Receiver",
        receiver_phone="+919876543210",
        receiver_address="456 Test Ave",
        receiver_city="Bangalore",
        receiver_state="Karnataka",
        receiver_zipcode="560001",
        parcel_type="documents",
        parcel_weight=1.0,
        pickup_date=date.today(),
        pickup_time=time(10, 0)
    )
    
    # Accept request - triggers 'request_accepted' notification
    pickup.status = 'accepted'
    pickup.save()
    
    # Assign driver - triggers 'driver_assigned' notification
    pickup.assigned_driver = driver
    pickup.save()
    
    # Check logs
    tail -f logs/whatsapp.log
"""
