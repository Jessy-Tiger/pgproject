from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta
from decimal import Decimal
import random
import string
import logging

from .models import UserProfile, PickupRequest, Invoice, ActivityLog, PICKUP_STATUS_CHOICES, WhatsAppOTP
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm,
    PickupRequestForm, AdminActionForm, DriverStatusUpdateForm, DriverCreationForm
)
from .utils import send_whatsapp_notification, generate_invoice_pdf

# Configure logger for views
logger = logging.getLogger(__name__)


# ============ UTILITY FUNCTIONS ============

def get_available_driver():
    """
    Get the best available driver for assignment based on workload.
    Returns the driver with fewest pending assignments, or None if no drivers available.
    """
    from django.db.models import Count
    
    available_drivers = User.objects.filter(
        profile__role='driver',
        profile__is_active_user=True
    ).annotate(
        pending_count=Count('assigned_pickups', filter=Q(assigned_pickups__status='pending_driver_acceptance'))
    ).order_by('pending_count')
    
    if available_drivers.exists():
        return available_drivers.first()
    return None


# ============ HOME PAGE ============

def home(request):
    """Home page view - route authenticated users to dashboard, others to login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


# ============ AUTHENTICATION VIEWS ============

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['email'].split('@')[0]
            user.save()
            
            # Create user profile as customer by default
            UserProfile.objects.create(user=user, role='customer')
            
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    context = {'form': form}
    return render(request, 'auth/register.html', context)


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate with username first, then email
        user = authenticate(request, username=username, password=password)
        if user is None:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username/email or password.')
    
    form = CustomAuthenticationForm()
    context = {'form': form}
    return render(request, 'auth/login.html', context)


def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


# ============ WHATSAPP PASSWORD RESET VIEWS ============

def whatsapp_password_reset(request):
    """Send OTP via WhatsApp for password reset"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email_or_phone = request.POST.get('email_or_phone', '').strip()
        
        # Find user by email or username
        try:
            user = User.objects.get(Q(email=email_or_phone) | Q(username=email_or_phone))
        except User.DoesNotExist:
            messages.error(request, 'No user found with this email or username.')
            return render(request, 'registration/password_reset_form.html')
        
        # Get user's phone number from profile
        try:
            user_profile = user.profile
            phone_number = user_profile.phone_number
        except UserProfile.DoesNotExist:
            messages.error(request, 'Please complete your profile first with a phone number.')
            return render(request, 'registration/password_reset_form.html')
        
        if not phone_number or phone_number.strip() == '':
            messages.error(request, 'No phone number found in your profile. Please update your profile.')
            return render(request, 'registration/password_reset_form.html')
        
        # Generate 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Set expiration time (10 minutes)
        expires_at = timezone.now() + timedelta(minutes=10)
        
        # Save or update OTP record
        WhatsAppOTP.objects.filter(user=user).delete()  # Delete old OTPs
        otp_record = WhatsAppOTP.objects.create(
            user=user,
            phone_number=phone_number,
            otp_code=otp_code,
            expires_at=expires_at
        )
        
        # Format phone number for WhatsApp
        whatsapp_phone = phone_number
        if not whatsapp_phone.startswith('+'):
            whatsapp_phone = '+91' + whatsapp_phone.lstrip('0')
        
        # Send OTP via WhatsApp
        from .utils import send_whatsapp_message
        message = f"""🔐 *VRL Logistics - Password Reset*

Your password reset OTP is:

*{otp_code}*

This OTP will expire in 10 minutes.

Do not share this code with anyone.

If you didn't request this, please ignore this message."""
        
        message_sid = send_whatsapp_message(
            phone_number=whatsapp_phone,
            message=message,
            message_type='password_reset_otp'
        )
        
        if message_sid:
            messages.success(request, f'OTP sent to {phone_number}. Please check your WhatsApp.')
            return redirect('whatsapp_otp_verify', user_id=user.id)
        else:
            messages.error(request, 'Failed to send OTP. Please try again.')
            return render(request, 'registration/password_reset_form.html')
    
    return render(request, 'registration/password_reset_form.html')


def whatsapp_otp_verify(request, user_id):
    """Verify OTP for password reset"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')
    
    try:
        otp_record = WhatsAppOTP.objects.get(user=user)
    except WhatsAppOTP.DoesNotExist:
        messages.error(request, 'OTP not found. Please request a new one.')
        return redirect('whatsapp_password_reset')
    
    # Check if OTP is expired
    if otp_record.is_expired():
        otp_record.delete()
        messages.error(request, 'OTP has expired. Please request a new one.')
        return redirect('whatsapp_password_reset')
    
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        
        # Check if user has exceeded attempts
        if not otp_record.is_valid_attempt():
            otp_record.delete()
            messages.error(request, 'Too many invalid attempts. Please request a new OTP.')
            return redirect('whatsapp_password_reset')
        
        # Verify OTP
        if entered_otp == otp_record.otp_code:
            otp_record.is_verified = True
            otp_record.save()
            messages.success(request, 'OTP verified! Now set your new password.')
            return redirect('whatsapp_password_reset_confirm', user_id=user.id)
        else:
            otp_record.attempts += 1
            otp_record.save()
            remaining_attempts = 3 - otp_record.attempts
            if remaining_attempts > 0:
                messages.error(request, f'Invalid OTP. {remaining_attempts} attempts remaining.')
            else:
                otp_record.delete()
                messages.error(request, 'Too many invalid attempts. Please request a new OTP.')
                return redirect('whatsapp_password_reset')
    
    context = {
        'user': user,
        'otp_record': otp_record,
    }
    return render(request, 'registration/password_reset_otp_verify.html', context)


def whatsapp_password_reset_confirm(request, user_id):
    """Set new password after OTP verification"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')
    
    try:
        otp_record = WhatsAppOTP.objects.get(user=user)
    except WhatsAppOTP.DoesNotExist:
        messages.error(request, 'OTP verification required first.')
        return redirect('whatsapp_password_reset')
    
    # Check if OTP is verified
    if not otp_record.is_verified:
        messages.error(request, 'Please verify OTP first.')
        return redirect('whatsapp_otp_verify', user_id=user.id)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validate passwords
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        elif new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Delete OTP record
            otp_record.delete()
            
            messages.success(request, 'Password reset successfully! Please login with your new password.')
            return redirect('login')
    
    context = {
        'user': user,
    }
    return render(request, 'registration/password_reset_confirm.html', context)


# ============ DASHBOARD ROUTING ============

@login_required(login_url='login')
def dashboard(request):
    """Route users to their respective dashboards based on role"""
    try:
        user_profile = request.user.profile
        role = user_profile.role
        
        if role == 'customer':
            return redirect('customer_dashboard')
        elif role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'driver':
            return redirect('driver_dashboard')
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Please complete your profile.')
        return redirect('complete_profile')
    
    return redirect('customer_dashboard')


# ============ CUSTOMER VIEWS ============

@login_required(login_url='login')
def customer_dashboard(request):
    """Customer dashboard view"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'customer':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    # Get customer's pickup requests
    pickup_requests = PickupRequest.objects.filter(customer=request.user).order_by('-created_at')
    
    # Statistics
    total_requests = pickup_requests.count()
    pending_requests = pickup_requests.filter(status='pending').count()
    completed_requests = pickup_requests.filter(status='delivered').count()
    
    # Recent requests (last 5)
    recent_requests = pickup_requests[:5]
    
    context = {
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'completed_requests': completed_requests,
        'recent_requests': recent_requests,
    }
    
    return render(request, 'customer/dashboard.html', context)


@login_required(login_url='login')
def create_pickup_request(request):
    """Create a new pickup request"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'customer':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PickupRequestForm(request.POST)
        if form.is_valid():
            pickup_request = form.save(commit=False)
            pickup_request.customer = request.user
            
            # Generate tracking number
            tracking_number = 'TRK' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            pickup_request.tracking_number = tracking_number
            
            pickup_request.save()
            
            # Log activity
            ActivityLog.objects.create(
                pickup_request=pickup_request,
                user=request.user,
                action='Pickup request created',
                status_after='pending'
            )
            
            # Send WhatsApp notifications
            send_whatsapp_notification(
                pickup_request=pickup_request,
                notification_type='new_request',
                recipient_role='admin'
            )
            
            # Inform user and redirect to their requests list
            messages.success(request,
                f'Pickup request created successfully! Tracking: {tracking_number}. Our admin team will review and accept your request shortly.')
            return redirect('view_pickup_requests')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PickupRequestForm()
    
    context = {'form': form}
    return render(request, 'customer/create_pickup.html', context)


@login_required(login_url='login')
def view_pickup_requests(request):
    """View all pickup requests (customer)"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'customer':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    pickup_requests = PickupRequest.objects.filter(customer=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        pickup_requests = pickup_requests.filter(status=status)
    
    context = {
        'pickup_requests': pickup_requests,
        'status_choices': PICKUP_STATUS_CHOICES,
    }
    
    return render(request, 'customer/view_requests.html', context)


@login_required(login_url='login')
def view_request_detail(request, pickup_id):
    """View details of a specific pickup request"""
    pickup_request = get_object_or_404(PickupRequest, id=pickup_id)
    
    # Check if user has permission
    if pickup_request.customer != request.user and request.user.profile.role != 'admin' and request.user.profile.role != 'driver':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    activity_logs = pickup_request.activity_logs.all().order_by('-timestamp')
    
    context = {
        'pickup_request': pickup_request,
        'activity_logs': activity_logs,
    }
    
    return render(request, 'shared/request_detail.html', context)


# ============ ADMIN VIEWS ============

@login_required(login_url='login')
def admin_dashboard(request):
    """Admin dashboard view"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'admin':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    # Get statistics
    total_requests = PickupRequest.objects.count()
    pending_requests = PickupRequest.objects.filter(status='pending').count()
    accepted_requests = PickupRequest.objects.filter(status__in=['accepted', 'assigned', 'pending_driver_acceptance']).count()
    delivered_requests = PickupRequest.objects.filter(status='delivered').count()
    
    # Recent requests
    recent_requests = PickupRequest.objects.order_by('-created_at')[:10]
    
    # Pending requests
    pending = PickupRequest.objects.filter(status='pending').order_by('-created_at')[:5]
    
    # All requests with filtering
    all_requests = PickupRequest.objects.all().order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        all_requests = all_requests.filter(status=status)
    
    # Search
    search = request.GET.get('search')
    if search:
        all_requests = all_requests.filter(
            Q(customer__first_name__icontains=search) |
            Q(customer__last_name__icontains=search) |
            Q(tracking_number__icontains=search)
        )
    
    # Drivers and customers
    drivers = User.objects.filter(profile__role='driver').order_by('-date_joined')
    customers = User.objects.filter(profile__role='customer').order_by('-date_joined')
    
    context = {
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'accepted_requests': accepted_requests,
        'delivered_requests': delivered_requests,
        'recent_requests': recent_requests,
        'pending_requests_list': pending,
        'all_requests': all_requests,
        'drivers': drivers,
        'customers': customers,
        'status_choices': PICKUP_STATUS_CHOICES,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required(login_url='login')
def view_all_requests(request):
    """View all pickup requests (admin)"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'admin':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    pickup_requests = PickupRequest.objects.all().order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        pickup_requests = pickup_requests.filter(status=status)
    
    # Search
    search = request.GET.get('search')
    if search:
        pickup_requests = pickup_requests.filter(
            Q(customer__first_name__icontains=search) |
            Q(customer__last_name__icontains=search) |
            Q(tracking_number__icontains=search)
        )
    
    context = {
        'pickup_requests': pickup_requests,
        'status_choices': PICKUP_STATUS_CHOICES,
    }
    
    return render(request, 'admin/view_requests.html', context)


@login_required(login_url='login')
def process_request(request, pickup_id):
    """Admin view to accept/reject a request"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'admin':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    pickup_request = get_object_or_404(PickupRequest, id=pickup_id)
    
    if request.method == 'POST':
        form = AdminActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            estimated_cost = form.cleaned_data['estimated_cost']
            assigned_driver = form.cleaned_data.get('assigned_driver')
            
            pickup_request.estimated_cost = estimated_cost
            
            if action == 'accept':
                # Use auto-assignment if no driver selected
                if not assigned_driver:
                    assigned_driver = get_available_driver()
                    if not assigned_driver:
                        messages.error(request, 'No available drivers to assign. Please try again later.')
                        return redirect('view_all_requests')
                
                pickup_request.status = 'pending_driver_acceptance'
                pickup_request.assigned_driver = assigned_driver
                
                # Generate invoice
                invoice_number = 'INV' + ''.join(random.choices(string.digits, k=8))
                invoice = Invoice.objects.create(
                    pickup_request=pickup_request,
                    invoice_number=invoice_number,
                    base_charge=estimated_cost * Decimal('0.8'),
                    tax=estimated_cost * Decimal('0.2'),
                    total_amount=estimated_cost,
                )
                
                pickup_request.save()
                
                # Log activity
                ActivityLog.objects.create(
                    pickup_request=pickup_request,
                    user=request.user,
                    action=f'Request accepted and assigned to driver {assigned_driver.first_name} {assigned_driver.last_name}',
                    status_before='pending',
                    status_after='pending_driver_acceptance'
                )
                
                # Send acceptance notification to customer
                send_whatsapp_notification(
                    pickup_request=pickup_request,
                    notification_type='request_accepted',
                    recipient_role='customer'
                )
                
                # Send assignment email to driver
                send_whatsapp_notification(
                    pickup_request=pickup_request,
                    notification_type='driver_assigned',
                    recipient_role='driver'
                )
                
                messages.success(request, f'Request accepted and assigned to {assigned_driver.first_name} {assigned_driver.last_name}!')
                
            else:  # reject
                rejection_reason = form.cleaned_data.get('rejection_reason', '')
                pickup_request.status = 'rejected'
                pickup_request.save()
                
                # Log activity
                ActivityLog.objects.create(
                    pickup_request=pickup_request,
                    user=request.user,
                    action='Request rejected by admin',
                    status_before='pending',
                    status_after='rejected',
                    notes=rejection_reason
                )
                
                # Send rejection notification
                send_whatsapp_notification(
                    pickup_request=pickup_request,
                    notification_type='request_rejected',
                    recipient_role='customer',
                    reason=rejection_reason
                )
                
                messages.success(request, 'Request rejected.')
            
            return redirect('admin_dashboard')
    else:
        form = AdminActionForm()
    
    context = {
        'pickup_request': pickup_request,
        'form': form,
    }
    
    return render(request, 'admin/process_request.html', context)


@login_required(login_url='login')
def assign_driver(request, pickup_id):
    """Assign a driver to a pickup request"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'admin':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    pickup_request = get_object_or_404(PickupRequest, id=pickup_id)
    
    if request.method == 'POST':
        driver_id = request.POST.get('driver_id')
        driver = get_object_or_404(User, id=driver_id)
        
        pickup_request.assigned_driver = driver
        pickup_request.status = 'pending_driver_acceptance'
        pickup_request.save()
        
        # Log activity
        ActivityLog.objects.create(
            pickup_request=pickup_request,
            user=request.user,
            action=f'Request assigned to driver {driver.first_name} {driver.last_name} (pending acceptance)',
            status_before='accepted',
            status_after='pending_driver_acceptance'
        )
        
        # Send notification to driver
        send_whatsapp_notification(
            pickup_request=pickup_request,
            notification_type='driver_assigned',
            recipient_role='driver'
        )
        
        messages.success(request, 'Driver assigned successfully!')
        return redirect('admin_dashboard')
    
    # Get available drivers
    drivers = User.objects.filter(profile__role='driver', profile__is_active_user=True)
    
    context = {
        'pickup_request': pickup_request,
        'drivers': drivers,
    }
    
    return render(request, 'admin/assign_driver.html', context)


@login_required(login_url='login')
def manage_drivers(request):
    """Manage drivers (admin)"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'admin':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    drivers = User.objects.filter(profile__role='driver').order_by('-date_joined')
    
    context = {
        'drivers': drivers,
    }
    
    return render(request, 'admin/manage_drivers.html', context)


@login_required(login_url='login')
def add_driver(request):
    """Add a new driver (admin)"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'admin':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DriverCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['email'].split('@')[0] + '_driver'
            user.save()
            
            # Create user profile as driver
            UserProfile.objects.create(
                user=user, 
                role='driver',
                phone_number=form.cleaned_data['phone_number']
            )
            
            messages.success(request, f'Driver {user.first_name} {user.last_name} added successfully! Username: {user.username}')
            return redirect('manage_drivers')
    else:
        form = DriverCreationForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'admin/add_driver.html', context)


@login_required(login_url='login')
def manage_customers(request):
    """Manage customers (admin)"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'admin':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    customers = User.objects.filter(profile__role='customer').order_by('-date_joined')
    
    context = {
        'customers': customers,
    }
    
    return render(request, 'admin/manage_customers.html', context)


# ============ DRIVER VIEWS ============

@login_required(login_url='login')
def driver_dashboard(request):
    """Driver dashboard view"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'driver':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    # Get assigned pickups
    assigned_pickups = PickupRequest.objects.filter(assigned_driver=request.user).order_by('-created_at')
    
    # Statistics
    total_assigned = assigned_pickups.filter(status__in=['assigned', 'pending_driver_acceptance']).count()
    picked_up = assigned_pickups.filter(status='picked_up').count()
    in_transit = assigned_pickups.filter(status='in_transit').count()
    delivered = assigned_pickups.filter(status='delivered').count()
    
    # Recent assignments
    recent_pickups = assigned_pickups[:5]
    
    context = {
        'total_assigned': total_assigned,
        'picked_up': picked_up,
        'in_transit': in_transit,
        'delivered': delivered,
        'recent_pickups': recent_pickups,
    }
    
    return render(request, 'driver/dashboard.html', context)


@login_required(login_url='login')
def driver_assigned_pickups(request):
    """View assigned pickups (driver)"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'driver':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    assigned_pickups = PickupRequest.objects.filter(assigned_driver=request.user).order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        assigned_pickups = assigned_pickups.filter(status=status)
    
    context = {
        'assigned_pickups': assigned_pickups,
        'status_choices': PICKUP_STATUS_CHOICES,
    }
    
    return render(request, 'driver/assigned_pickups.html', context)


@login_required(login_url='login')
def update_pickup_status(request, pickup_id):
    """Driver updates pickup status"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'driver':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    pickup_request = get_object_or_404(PickupRequest, id=pickup_id, assigned_driver=request.user)
    
    if request.method == 'POST':
        form = DriverStatusUpdateForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            notes = form.cleaned_data.get('notes', '')
            
            old_status = pickup_request.status
            pickup_request.status = new_status
            
            if new_status == 'delivered':
                pickup_request.completed_at = timezone.now()
            
            pickup_request.save()
            
            # Log activity
            ActivityLog.objects.create(
                pickup_request=pickup_request,
                user=request.user,
                action=f'Status updated to {new_status}',
                status_before=old_status,
                status_after=new_status,
                notes=notes
            )
            
            # Send notification to customer
            send_whatsapp_notification(
                pickup_request=pickup_request,
                notification_type='assignment_accepted',
                recipient_role='driver'
            )
            
            messages.success(request, f'Status updated to {new_status}!')
            return redirect('driver_assigned_pickups')
    else:
        form = DriverStatusUpdateForm()
    
    context = {
        'pickup_request': pickup_request,
        'form': form,
    }
    
    return render(request, 'driver/update_status.html', context)


@login_required(login_url='login')
def accept_assignment(request, pickup_id):
    """Driver accepts an assignment"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'driver':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    pickup_request = get_object_or_404(PickupRequest, id=pickup_id, assigned_driver=request.user, status='pending_driver_acceptance')
    
    pickup_request.status = 'assigned'
    pickup_request.save()
    
    # Log activity
    ActivityLog.objects.create(
        pickup_request=pickup_request,
        user=request.user,
        action='Assignment accepted by driver',
        status_before='pending_driver_acceptance',
        status_after='assigned'
    )
    
    # Send emails with error handling - don't let email failures break the user workflow
    whatsapp_sent = True
    try:
        # Send acceptance notification to customer
        if not send_whatsapp_notification(
            pickup_request=pickup_request,
            notification_type='request_accepted',
            recipient_role='customer'
        ):
            whatsapp_sent = False
    except Exception as e:
        logger.error(f"Failed to send acceptance notification to customer for pickup {pickup_id}: {str(e)}")
        whatsapp_sent = False
    
    try:
        # Send confirmation notification to driver
        if not send_whatsapp_notification(
            pickup_request=pickup_request,
            notification_type='assignment_accepted',
            recipient_role='driver'
        ):
            whatsapp_sent = False
    except Exception as e:
        logger.error(f"Failed to send confirmation notification to driver for pickup {pickup_id}: {str(e)}")
        whatsapp_sent = False
    
    try:
        # Send confirmation notification to admin
        if not send_whatsapp_notification(
            pickup_request=pickup_request,
            notification_type='assignment_accepted',
            recipient_role='admin'
        ):
            whatsapp_sent = False
    except Exception as e:
        logger.error(f"Failed to send confirmation notification to admin for pickup {pickup_id}: {str(e)}")
        whatsapp_sent = False
    
    # Show appropriate success message
    if not whatsapp_sent:
        messages.warning(request, 'Assignment accepted successfully! (Some notification messages could not be sent)')
    else:
        messages.success(request, 'Assignment accepted successfully!')
    
    return redirect('driver_assigned_pickups')


@login_required(login_url='login')
def reject_assignment(request, pickup_id):
    """Driver rejects an assignment"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role != 'driver':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    pickup_request = get_object_or_404(PickupRequest, id=pickup_id, assigned_driver=request.user, status='pending_driver_acceptance')
    
    # Find another driver to assign to
    other_drivers = User.objects.filter(profile__role='driver', profile__is_active_user=True).exclude(id=request.user.id)
    
    if other_drivers.exists():
        # Assign to the first available driver (can be improved with load balancing)
        next_driver = other_drivers.first()
        pickup_request.assigned_driver = next_driver
        pickup_request.status = 'pending_driver_acceptance'
        pickup_request.save()
        
        # Log activity
        ActivityLog.objects.create(
            pickup_request=pickup_request,
            user=request.user,
            action=f'Assignment rejected by driver, reassigned to {next_driver.first_name} {next_driver.last_name}',
            status_before='pending_driver_acceptance',
            status_after='pending_driver_acceptance'
        )
        
        # Send notifications with error handling
        try:
            # Send reassignment notification to customer
            send_whatsapp_notification(
                pickup_request=pickup_request,
                notification_type='assignment_reassigned',
                recipient_role='customer',
                reason='Driver reassigned'
            )
        except Exception as e:
            logger.error(f"Failed to send reassignment notification to customer for pickup {pickup_id}: {str(e)}")
        
        try:
            # Send notification to new driver
            send_whatsapp_notification(
                pickup_request=pickup_request,
                notification_type='driver_assigned',
                recipient_role='driver'
            )
        except Exception as e:
            logger.error(f"Failed to send assignment notification to new driver for pickup {pickup_id}: {str(e)}")
        
        messages.info(request, f'Assignment rejected and reassigned to another driver.')
    else:
        # No other drivers available, set back to accepted
        pickup_request.assigned_driver = None
        pickup_request.status = 'accepted'
        pickup_request.save()
        
        # Log activity
        ActivityLog.objects.create(
            pickup_request=pickup_request,
            user=request.user,
            action='Assignment rejected by driver, no other drivers available',
            status_before='pending_driver_acceptance',
            status_after='accepted'
        )
        
        # Send notification to customer about lack of drivers with error handling
        try:
            send_whatsapp_notification(
                pickup_request=pickup_request,
                notification_type='assignment_waiting',
                recipient_role='customer',
                reason='No drivers available, will retry soon'
            )
        except Exception as e:
            logger.error(f"Failed to send 'waiting' notification to customer for pickup {pickup_id}: {str(e)}")
        
        messages.warning(request, 'Assignment rejected. No other drivers available - admin will handle reassignment.')
    
    return redirect('driver_assigned_pickups')


# ============ PROFILE VIEWS ============

@login_required(login_url='login')
def complete_profile(request):
    """Complete user profile"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            # update the user email field as well
            email = form.cleaned_data.get('email')
            if email and email != request.user.email:
                request.user.email = email
                request.user.save()
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
    else:
        # prefill email from user account
        initial_data = {'email': request.user.email}
        form = UserProfileForm(instance=user_profile, initial=initial_data)
    
    context = {'form': form}
    return render(request, 'profile/complete_profile.html', context)


@login_required(login_url='login')
def view_profile(request):
    """View the logged-in user's profile"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    context = {'user_profile': user_profile}
    return render(request, 'profile/view_profile.html', context)


@login_required(login_url='login')
def admin_view_user_profile(request, user_id):
    """Allow an admin to view another user's profile"""
    user_profile = get_object_or_404(UserProfile, user__id=user_id)
    # ensure only admins can access this
    if request.user.profile.role != 'admin':
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    context = {'user_profile': user_profile, 'admin_view': True}
    return render(request, 'profile/view_profile.html', context)


# ============ API VIEWS ============

@login_required(login_url='login')
@require_http_methods(["GET"])
def get_request_stats(request):
    """Get request statistics (JSON for charts)"""
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if user_profile.role == 'customer':
        requests = PickupRequest.objects.filter(customer=request.user)
    elif user_profile.role == 'admin':
        requests = PickupRequest.objects.all()
    elif user_profile.role == 'driver':
        requests = PickupRequest.objects.filter(assigned_driver=request.user)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get last 30 days data
    last_30_days = timezone.now() - timedelta(days=30)
    requests_last_30 = requests.filter(created_at__gte=last_30_days)
    
    # Status breakdown
    status_data = {}
    for status_value, status_label in PICKUP_STATUS_CHOICES:
        count = requests.filter(status=status_value).count()
        status_data[status_label] = count
    
    # Daily requests for last 30 days
    daily_data = []
    for i in range(30):
        date = timezone.now() - timedelta(days=30-i)
        count = requests_last_30.filter(created_at__date=date.date()).count()
        daily_data.append({'date': date.strftime('%Y-%m-%d'), 'count': count})
    
    return JsonResponse({
        'status_data': status_data,
        'daily_data': daily_data,
        'total_requests': requests.count(),
    })

