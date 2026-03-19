from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Customer URLs
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/create-pickup/', views.create_pickup_request, name='create_pickup_request'),
    path('customer/pickups/', views.view_pickup_requests, name='view_pickup_requests'),
    
    # Shared URLs
    path('request/<int:pickup_id>/', views.view_request_detail, name='view_request_detail'),
    
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/requests/', views.view_all_requests, name='view_all_requests'),
    path('admin/request/<int:pickup_id>/process/', views.process_request, name='process_request'),
    path('admin/request/<int:pickup_id>/assign-driver/', views.assign_driver, name='assign_driver'),
    path('admin/drivers/', views.manage_drivers, name='manage_drivers'),
    path('admin/drivers/add/', views.add_driver, name='add_driver'),
    path('admin/customers/', views.manage_customers, name='manage_customers'),
    path('admin/user/<int:user_id>/', views.admin_view_user_profile, name='admin_view_user_profile'),
    
    # Driver URLs
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('driver/assigned-pickups/', views.driver_assigned_pickups, name='driver_assigned_pickups'),
    path('driver/pickup/<int:pickup_id>/update-status/', views.update_pickup_status, name='update_pickup_status'),
    path('driver/pickup/<int:pickup_id>/accept/', views.accept_assignment, name='accept_assignment'),
    path('driver/pickup/<int:pickup_id>/reject/', views.reject_assignment, name='reject_assignment'),
    
    # Profile URLs
    path('profile/complete/', views.complete_profile, name='complete_profile'),
    path('profile/', views.view_profile, name='view_profile'),
    
    # Password Reset URLs - WhatsApp OTP
    path('password-reset/', views.whatsapp_password_reset, name='password_reset'),
    path('otp-verify/<int:user_id>/', views.whatsapp_otp_verify, name='whatsapp_otp_verify'),
    path('password-reset-confirm/<int:user_id>/', views.whatsapp_password_reset_confirm, name='whatsapp_password_reset_confirm'),
    
    # Legacy Password Reset URLs (kept for compatibility)
    # path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    # path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # API URLs
    path('api/request-stats/', views.get_request_stats, name='get_request_stats'),
]
