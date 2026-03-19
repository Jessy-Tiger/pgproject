import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vrllogistics.settings')
django.setup()

from django.contrib.auth.models import User
from vrllog.models import UserProfile

admins = User.objects.filter(profile__role='admin')
print('Admin users:')
if admins.exists():
    for u in admins:
        phone = u.profile.phone_number if hasattr(u, 'profile') else 'N/A'
        print(f'  {u.username} - {u.email} - Phone: {phone}')
else:
    print('  No admin users found')

print('\nAll users:')
all_users = User.objects.all()
for u in all_users:
    role = u.profile.role if hasattr(u, 'profile') else 'N/A'
    phone = u.profile.phone_number if hasattr(u, 'profile') else 'N/A'
    print(f'  {u.username} ({role}) - {u.email} - Phone: {phone}')
