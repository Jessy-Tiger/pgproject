from django.contrib import admin
from .models import UserProfile, PickupRequest, Invoice, ActivityLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'city', 'created_at')
    list_filter = ('role', 'created_at', 'is_active_user')
    search_fields = ('user__username', 'user__email', 'phone_number', 'city')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'is_active_user')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'address', 'city', 'state', 'zipcode')
        }),
        ('Profile Picture', {
            'fields': ('profile_picture',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PickupRequest)
class PickupRequestAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'customer', 'status', 'sender_name', 'receiver_name', 'parcel_type', 'created_at')
    list_filter = ('status', 'parcel_type', 'created_at', 'pickup_date')
    search_fields = ('tracking_number', 'customer__username', 'sender_name', 'receiver_name')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'tracking_number')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('customer', 'tracking_number', 'status', 'assigned_driver', 'created_at', 'updated_at', 'completed_at')
        }),
        ('Sender Details', {
            'fields': ('sender_name', 'sender_phone', 'sender_address', 'sender_city', 'sender_state', 'sender_zipcode')
        }),
        ('Receiver Details', {
            'fields': ('receiver_name', 'receiver_phone', 'receiver_address', 'receiver_city', 'receiver_state', 'receiver_zipcode')
        }),
        ('Parcel Details', {
            'fields': ('parcel_type', 'parcel_weight', 'parcel_description')
        }),
        ('Pickup Information', {
            'fields': ('pickup_date', 'pickup_time', 'additional_notes')
        }),
        ('Pricing', {
            'fields': ('estimated_cost',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('customer', 'sender_name', 'receiver_name')
        return self.readonly_fields


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'pickup_request', 'total_amount', 'is_paid', 'issued_date')
    list_filter = ('is_paid', 'issued_date')
    search_fields = ('invoice_number', 'pickup_request__tracking_number')
    readonly_fields = ('issued_date', 'pickup_request')
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'pickup_request', 'issued_date', 'due_date')
        }),
        ('Charges', {
            'fields': ('base_charge', 'weight_charge', 'tax', 'total_amount')
        }),
        ('Payment', {
            'fields': ('is_paid', 'paid_date')
        }),
        ('PDF', {
            'fields': ('pdf_file',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('pickup_request', 'user', 'action', 'status_before', 'status_after', 'timestamp')
    list_filter = ('timestamp', 'status_after')
    search_fields = ('pickup_request__tracking_number', 'user__username', 'action')
    readonly_fields = ('pickup_request', 'user', 'timestamp', 'action', 'status_before', 'status_after', 'notes')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
