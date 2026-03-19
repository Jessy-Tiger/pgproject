# VRL Logistics - Doorstep Pickup System
## Complete Implementation Guide

### Project Overview
A professional web application for managing doorstep pickup requests in a courier company. The system includes role-based access control for customers, admins, and drivers with complete workflow automation.

---

## 📋 System Features Implemented

### ✅ Authentication & Authorization
- User registration with email validation
- Role-based login system (Customer, Admin, Driver)
- Session management
- Protected views with login_required decorator
- Role-based dashboard routing

### ✅ Database Models
- **UserProfile**: Extended user model with role, contact info, address
- **PickupRequest**: Complete pickup request with sender/receiver details
- **Invoice**: Invoice generation with charge breakdown
- **ActivityLog**: Track all request status changes and actions

### ✅ Customer Module
- Create pickup requests with complete details
- View request history and status
- Real-time status tracking
- Request details with activity timeline

### ✅ Admin Module
- View all pickup requests with advanced filtering
- Accept/reject requests with cost estimation
- Assign drivers to accepted requests
- Manage customers and drivers
- Generate invoices automatically
- Dashboard with statistics

### ✅ Driver Module
- View assigned pickups
- Update delivery status (picked up, in transit, delivered)
- Real-time request details
- Assignment notifications

### ✅ Email Notification System
- New request notifications to admins
- Request acceptance/rejection to customers
- Driver assignment notifications with confirmation
- Assignment acceptance/reassignment notifications
- Status update notifications to customers
- Invoice attachment in acceptance emails (PDF)
- Comprehensive logging of all email activities
- Defensive error handling prevents email failures from breaking workflows
- Environment-based configuration with security best practices
- 8 notification types: new_request, request_accepted, request_rejected, driver_assigned, status_update, assignment_accepted, assignment_reassigned, assignment_waiting
- Professional HTML templates with consistent branding

### ✅ UI/UX
- Bootstrap 5-based responsive design
- Clean, professional interface
- Icon integration with Font Awesome
- Mobile-friendly layouts
- Proper Status badges and visualizations

---

## 🚀 Quick Start Guide

### Step 1: Activate Virtual Environment
```bash
cd c:\Users\muthu\Desktop\PGProject
env\Scripts\activate
```

### Step 2: Install Required Packages
```bash
pip install django==6.0.3 reportlab python-dateutil pillow
```

### Step 3: Run Migrations
```bash
cd vrllogistics
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Create Superuser (Admin)
```bash
python manage.py createsuperuser
# Follow the prompts to create admin account
```

### Step 5: Configure Email Settings
Edit `vrllogistics/settings.py` and update:
```python
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-specific-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

**Note**: For Gmail:
1. Enable 2-Factor Authentication
2. Generate App Password at https://myaccount.google.com/apppasswords
3. Use the generated 16-character password

### Step 6: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 7: Run Development Server
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000/

---

## 📁 Project Structure

```
vrllogistics/
├── vrllogistics/          # Project configuration
│   ├── settings.py       # All project settings
│   ├── urls.py           # Main URL routing
│   ├── wsgi.py           # WSGI config
│   └── asgi.py           # ASGI config
│
├── vrllog/               # Main app
│   ├── models.py         # Database models
│   ├── views.py          # View logic (500+ lines)
│   ├── forms.py          # Django forms
│   ├── admin.py          # Admin configuration
│   ├── urls.py           # App URL routing
│   └── utils.py          # Email & PDF utilities
│
├── templates/
│   ├── base.html         # Base template
│   ├── auth/             # Login, Register
│   ├── customer/         # Customer templates
│   ├── admin/            # Admin templates
│   ├── driver/           # Driver templates
│   ├── shared/           # Shared templates
│   ├── profile/          # Profile templates
│   └── emails/           # Email templates (HTML)
│
├── static/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── js/
│       └── main.js       # JavaScript utilities
│
└── manage.py             # Django management
```

---

## 🔑 User Credentials (After Setup)

### Login URLs
- **Main Login**: `/login/`
- **Register**: `/register/`
- **Dashboard**: `/dashboard/`
- **Admin Panel**: `/admin/`

### Test Accounts (Create via register page)

1. **Customer Account**
   - Use registration form
   - Role auto-set to 'customer'
   - Access customer dashboard

2. **Admin Account**
   - Create via management command or Django admin
   - Add UserProfile with role='admin'
   - Access `/admin/dashboard/`

3. **Driver Account**
   - Create via management command or Django admin
   - Add UserProfile with role='driver'
   - Access `/driver/dashboard/`

---

## 🛣️ API Endpoints

### Authentication
- `GET /login/` - Login page
- `POST /login/` - Handle login
- `GET /register/` - Registration page
- `POST /register/` - Handle registration
- `GET /logout/` - Logout

### Customer Routes
- `GET /dashboard/` - Route to role dashboard
- `GET /customer/dashboard/` - Customer dashboard
- `GET /customer/create-pickup/` - Create request form
- `POST /customer/create-pickup/` - Submit request
- `GET /customer/pickups/` - View all requests
- `GET /request/<id>/` - View request details

### Admin Routes
- `GET /admin/dashboard/` - Admin dashboard
- `GET /admin/requests/` - View all requests
- `GET /admin/request/<id>/process/` - Process request
- `POST /admin/request/<id>/process/` - Accept/Reject
- `GET /admin/request/<id>/assign-driver/` - Assign driver
- `POST /admin/request/<id>/assign-driver/` - Submit assignment
- `GET /admin/drivers/` - Manage drivers
- `GET /admin/customers/` - Manage customers

### Driver Routes
- `GET /driver/dashboard/` - Driver dashboard
- `GET /driver/assigned-pickups/` - View assignments
- `GET /driver/pickup/<id>/update-status/` - Update status form
- `POST /driver/pickup/<id>/update-status/` - Submit status

### Profile Routes
- `GET /profile/` - View profile
- `GET /profile/complete/` - Complete/Edit profile
- `POST /profile/complete/` - Save profile

### API Routes
- `GET /api/request-stats/` - Get statistics (JSON)

---

## 📧 Email Notification System (Production-Grade)

### Quick Setup (5 Minutes)
```bash
# 1. Copy environment template
cp vrllogistics/.env.example vrllogistics/.env

# 2. Edit .env with Gmail credentials
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx  (16-char app password)

# 3. Verify setup
python manage.py check

# 4. Monitor emails
tail -f vrllogistics/logs/email.log
```

### Email Notification Types
| Event | Recipient | Template | PDF Attachment |
|-------|-----------|----------|-----------------|
| New Request | Admin | `new_request_admin.html` | - |
| Request Accepted | Customer | `request_accepted_customer.html` | ✅ Invoice |
| Request Rejected | Customer | `request_rejected_customer.html` | - |
| Driver Assigned | Driver | `driver_assigned.html` | - |
| Status Update | Customer | `status_update_customer.html` | - |
| Assignment Accepted | Driver | `assignment_accepted_driver.html` | - |
| Assignment Reassigned | Customer | `assignment_reassigned_customer.html` | - |
| Assignment Waiting | Customer | `assignment_waiting_customer.html` | - |

### Key Features
✅ **Security**: Credentials in `.env` (not in code)
✅ **Logging**: All emails logged to `vrllogistics/logs/email.log`
✅ **Error Handling**: Email failures don't break workflows
✅ **Production-Ready**: Async-capable, load-tested patterns
✅ **Documentation**: 600+ lines of comprehensive guides
✅ **Professional**: HTML templates with consistent branding

### Configuration
- **Gmail SMTP**: Automatically configured in `settings.py`
- **Environment Variables**: Email credentials in `.env`
- **Logging Levels**: DEBUG for email.log, WARNING for django.log
- **Timeout**: 10 seconds (configurable)
- **Fallback**: Console backend in DEBUG mode

### Email System Documentation
For complete details, see:
- **[EMAIL_SYSTEM_QUICKSTART.md](EMAIL_SYSTEM_QUICKSTART.md)** - 5-minute setup + common tasks
- **[EMAIL_SYSTEM_DOCUMENTATION.md](EMAIL_SYSTEM_DOCUMENTATION.md)** - Full API and configuration (600+ lines)
- **[EMAIL_SYSTEM_EXAMPLES.md](EMAIL_SYSTEM_EXAMPLES.md)** - Code examples and patterns
- **[EMAIL_SYSTEM_IMPLEMENTATION.md](EMAIL_SYSTEM_IMPLEMENTATION.md)** - What changed and architecture

### Monitoring Emails
```bash
# View logs in real-time
tail -f vrllogistics/logs/email.log

# Count emails sent today
grep "$(date +%Y-%m-%d)" vrllogistics/logs/email.log | wc -l

# Find errors
grep "ERROR" vrllogistics/logs/email.log

# Search by notification type
grep "assignment_accepted" vrllogistics/logs/email.log
```

### Troubleshooting
- **Auth Failed**: Use app-specific password (not regular Gmail password)
- **Template Not Found**: Check template path in `vrllog/utils.py`
- **Connection Failed**: Verify EMAIL_HOST and EMAIL_PORT in settings.py
- **All Issues**: Check `vrllogistics/logs/email.log` - detailed error messages there

---

## 📧 Legacy Email Configuration (See above for new system)

## 🗄️ Database Models

### UserProfile
```python
- user (OneToOne with User)
- role (customer, admin, driver)
- phone_number, address, city, state, zipcode
- profile_picture
- is_active_user
```

### PickupRequest
```python
- customer (FK to User)
- Sender: name, phone, address, city, state, zipcode
- Receiver: name, phone, address, city, state, zipcode
- Parcel: type, weight, description
- Schedule: pickup_date, pickup_time
- Status: pending, accepted, assigned, picked_up, in_transit, delivered, rejected
- assigned_driver (FK to User)
- estimated_cost, tracking_number
```

### Invoice
```python
- pickup_request (OneToOne)
- invoice_number (unique)
- base_charge, weight_charge, tax, total_amount
- issued_date, due_date
- is_paid, paid_date
- pdf_file
```

### ActivityLog
```python
- pickup_request (FK)
- user (FK)
- action, status_before, status_after
- notes, timestamp
```

---

## 🎨 UI Components Used

### Layout
- Bootstrap 5 Grid system
- Responsive containers
- Flex utilities

### Components
- Navigation bar with user dropdown
- Alert messages (success, error, warning, info)
- Cards with shadows
- Data tables with hover effects
- Status badges
- Form inputs with validation
- Modal dialogs
- Dropdown menus
- Pagination

### Icons
- Font Awesome 6.4
- Used throughout for visual clarity

---

## 🔐 Security Features

### Implemented
- CSRF protection on all forms
- Password hashing
- Login required decorators
- Role-based access control
- SQL injection prevention (ORM)
- XSS protection (template escaping)

### Recommended Production Additions
- HTTPS/SSL configuration
- Rate limiting
- Input validation and sanitization
- Two-factor authentication
- API authentication tokens
- Regular security audits

---

## 🐛 Troubleshooting

### Issue: Email not sending
**Solution**: 
- Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in settings.py
- For Gmail, use App Password (not regular password)
- Enable "Less secure apps" if not using App Password
- Check internet connection

### Issue: Migrations fail
**Solution**:
```bash
python manage.py makemigrations vrllog
python manage.py migrate
```

### Issue: Static files not loading
**Solution**:
```bash
python manage.py collectstatic --noinput
# For development, Django auto-serves static files
```

### Issue: Database errors
**Solution**:
```bash
# Delete db.sqlite3 and re-run migrations
rm vrllogistics/db.sqlite3
python manage.py migrate
```

---

## ⚙️ Configuration Tips

### Change Default Currency
Edit `utils.py` in `generate_invoice_pdf()` function:
```python
# Look for "₹" symbols and replace currency symbol
```

### Customize Email Templates
Edit files in `templates/emails/`:
- `new_request_admin.html`
- `request_accepted_customer.html`
- `request_rejected_customer.html`
- `driver_assigned.html`
- `status_update_customer.html`

### Modify Styling
Edit `static/css/style.css`:
- Change primary color: `--primary-color: #0d6efd;`
- Add custom CSS for components
- Adjust responsive breakpoints

### Add Logo/Images
1. Create `static/images/` folder
2. Place images there
3. Reference in templates: `<img src="/static/images/logo.png">`

---

## 📊 Sample Data Setup

Create test accounts:
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from vrllog.models import UserProfile

# Create customer
customer = User.objects.create_user(
    username='customer1@example.com',
    email='customer1@example.com',
    password='testpass123',
    first_name='John',
    last_name='Doe'
)
UserProfile.objects.create(user=customer, role='customer', phone_number='9876543210')

# Create driver
driver = User.objects.create_user(
    username='driver1@example.com',
    email='driver1@example.com',
    password='testpass123',
    first_name='Mike',
    last_name='Smith'
)
UserProfile.objects.create(user=driver, role='driver', phone_number='9876543212')

# Create admin
admin = User.objects.create_user(
    username='admin@example.com',
    email='admin@example.com',
    password='testpass123',
    first_name='Admin',
    last_name='User'
)
UserProfile.objects.create(user=admin, role='admin', phone_number='9876543211')
```

---

## 🚢 Deployment Checklist

- [ ] Set `DEBUG = False` in settings.py
- [ ] Set appropriate `ALLOWED_HOSTS`
- [ ] Configure database (PostgreSQL recommended)
- [ ] Set up email service
- [ ] Configure STATIC_ROOT and MEDIA_ROOT
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS
- [ ] Set up backup strategy
- [ ] Configure web server (Gunicorn, Nginx)
- [ ] Set up monitoring/logging
- [ ] Test all functionality
- [ ] Document deployment process

---

## 📞 Support

For issues or clarifications:
1. Check the troubleshooting section
2. Review Django documentation
3. Check Email configuration
4. Verify all files are in correct locations
5. Ensure all pip packages are installed

---

## 📄 License & Credits

VRL Logistics Doorstep Pickup System  
Built with Django 6.0.3 and Bootstrap 5  
© 2024

---

## ✨ Next Steps

1. **Configure Email**: Update gmail credentials in settings.py
2. **Run Migrations**: Execute database setup
3. **Create Test Users**: Set up sample accounts
4. **Test All Workflows**: Go through each user role
5. **Customize Branding**: Update colors, logos, company details
6. **Deploy**: Follow deployment checklist

**Happy delivery! 📦**
