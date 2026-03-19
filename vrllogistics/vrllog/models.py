from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Role choices
ROLE_CHOICES = (
    ('customer', 'Customer'),
    ('admin', 'Admin/HR'),
    ('driver', 'Driver'),
)

# Parcel type choices
PARCEL_TYPE_CHOICES = (
    ('documents', 'Documents'),
    ('electronics', 'Electronics'),
    ('clothing', 'Clothing'),
    ('fragile', 'Fragile Items'),
    ('perishable', 'Perishable'),
    ('other', 'Other'),
)

# Status choices
PICKUP_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
    ('assigned', 'Assigned to Driver'),
    ('pending_driver_acceptance', 'Pending Driver Acceptance'),
    ('picked_up', 'Picked Up'),
    ('in_transit', 'In Transit'),
    ('delivered', 'Delivered'),
)


class UserProfile(models.Model):
    """Extended User profile with role-based functionality"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zipcode = models.CharField(max_length=10, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active_user = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


class PickupRequest(models.Model):
    """Model for storing pickup requests from customers"""
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pickup_requests')
    
    # Sender information
    sender_name = models.CharField(max_length=100)
    sender_phone = models.CharField(max_length=15)
    sender_address = models.TextField()
    sender_city = models.CharField(max_length=100)
    sender_state = models.CharField(max_length=100)
    sender_zipcode = models.CharField(max_length=10)
    sender_email = models.EmailField(max_length=254, blank=True, null=True)
    
    # Receiver information
    receiver_name = models.CharField(max_length=100)
    receiver_phone = models.CharField(max_length=15)
    receiver_address = models.TextField()
    receiver_city = models.CharField(max_length=100)
    receiver_state = models.CharField(max_length=100)
    receiver_zipcode = models.CharField(max_length=10)
    
    # Parcel details
    parcel_type = models.CharField(max_length=20, choices=PARCEL_TYPE_CHOICES)
    parcel_weight = models.DecimalField(max_digits=8, decimal_places=2, help_text="Weight in kg")
    parcel_description = models.TextField(blank=True, null=True)
    
    # Pickup details
    pickup_date = models.DateField()
    pickup_time = models.TimeField()
    additional_notes = models.TextField(blank=True, null=True)
    
    # Status and tracking
    status = models.CharField(max_length=30, choices=PICKUP_STATUS_CHOICES, default='pending')
    assigned_driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_pickups')
    
    # Pricing and tracking
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tracking_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Pickup #{self.id} - {self.sender_name} to {self.receiver_name}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Pickup Request"
        verbose_name_plural = "Pickup Requests"


class Invoice(models.Model):
    """Model for storing invoice information"""
    pickup_request = models.OneToOneField(PickupRequest, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    
    # Pricing breakdown
    base_charge = models.DecimalField(max_digits=10, decimal_places=2)
    weight_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Dates
    issued_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    
    # Status
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(blank=True, null=True)
    
    # PDF
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)

    def __str__(self):
        return f"Invoice {self.invoice_number}"

    class Meta:
        ordering = ['-issued_date']


class ActivityLog(models.Model):
    """Model for tracking user activities and status changes"""
    pickup_request = models.ForeignKey(PickupRequest, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    status_before = models.CharField(max_length=20, blank=True, null=True)
    status_after = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pickup_request.id} - {self.action}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"


class WhatsAppOTP(models.Model):
    """Model for storing WhatsApp OTP for password reset"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='whatsapp_otp')
    phone_number = models.CharField(max_length=15)
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"OTP for {self.user.username}"
    
    def is_expired(self):
        """Check if OTP has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_valid_attempt(self):
        """Check if user still has valid attempts"""
        return self.attempts < 3
    
    class Meta:
        verbose_name = "WhatsApp OTP"
        verbose_name_plural = "WhatsApp OTPs"
