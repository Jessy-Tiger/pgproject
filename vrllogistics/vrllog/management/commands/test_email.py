"""
Django management command to test email configuration.

Usage:
  python manage.py test_email                  # Test SMTP connection only
  python manage.py test_email --send           # Send test email to admin
  python manage.py test_email --send john@example.com  # Send to specific recipient
  python manage.py test_email --verbose        # Show detailed output
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from vrllog.email_service import test_email_connection, send_test_email, get_email_configuration


class Command(BaseCommand):
    help = 'Test email configuration and send test emails'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--send',
            nargs='?',
            const='admin',
            default=None,
            help='Send test email. Optional recipient email, defaults to admin email.'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output including full configuration'
        )
        parser.add_argument(
            '--config',
            action='store_true',
            help='Display current email configuration'
        )
    
    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        
        # Show configuration if requested
        if options.get('config'):
            self.show_configuration()
            return
        
        # Test connection first
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("🧪 EMAIL SYSTEM TEST"))
        self.stdout.write("=" * 80 + "\n")
        
        success, message = test_email_connection()
        
        if not success:
            self.stdout.write(self.style.ERROR(f"\n❌ Connection test failed:\n{message}"))
            raise CommandError("Email connection test failed. Check your configuration.")
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Connection test passed!\n{message}"))
        
        # Send test email if requested
        if options.get('send') is not None:
            recipient = options['send']
            
            # Use admin email if 'admin' specified
            if recipient.lower() == 'admin':
                recipient = settings.ADMIN_EMAIL
            
            self.stdout.write(f"\nSending test email to: {recipient}")
            
            if send_test_email(recipient):
                self.stdout.write(self.style.SUCCESS(f"✅ Test email sent to {recipient}"))
            else:
                raise CommandError(f"Failed to send test email to {recipient}")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Email test completed successfully!\n"))
    
    def show_configuration(self):
        """Display current email configuration"""
        config = get_email_configuration()
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("📧 EMAIL CONFIGURATION"))
        self.stdout.write("=" * 80 + "\n")
        
        for key, value in config.items():
            # Hide actual password
            if key == 'EMAIL_HOST_PASSWORD':
                display_value = "***" + value[-4:] if len(str(value)) > 4 else "***"
            else:
                display_value = value
            
            self.stdout.write(f"{key}: {display_value}")
        
        self.stdout.write("\n" + "=" * 80 + "\n")
