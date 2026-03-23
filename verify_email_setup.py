#!/usr/bin/env python
"""
VRL Logistics - Email Configuration Verification Script
========================================================

This script tests your email configuration without running Django server.

Usage:
    python verify_email_setup.py

It will:
1. Check .env file exists and has correct settings
2. Test SMTP connection to Gmail
3. Verify authentication
4. Send a test email
5. Report detailed errors if anything fails

Author: VRL Logistics
Date: March 23, 2026
"""

import os
import sys
import smtplib
import socket
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_success(text):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text):
    """Print error message"""
    print(f"❌ {text}")


def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")


def load_env_file():
    """Load .env file and return as dictionary"""
    env_path = Path(__file__).parent / '.env'
    
    if not env_path.exists():
        print_error(".env file not found at: " + str(env_path))
        return None
    
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        return env_vars
    except Exception as e:
        print_error(f"Failed to read .env file: {e}")
        return None


def check_env_configuration(env_vars):
    """Check if .env has all required email settings"""
    print_header("STEP 1: CHECK .ENV FILE")
    
    required_settings = [
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_USE_TLS',
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD',
        'DEFAULT_FROM_EMAIL',
        'ADMIN_EMAIL',
    ]
    
    print("Required settings to check:")
    all_present = True
    
    for setting in required_settings:
        if setting in env_vars:
            value = env_vars[setting]
            
            # Hide passwords
            if setting == 'EMAIL_HOST_PASSWORD':
                display_value = "***" + value[-4:] if len(value) > 4 else "***"
            else:
                display_value = value
            
            print_success(f"{setting}: {display_value}")
        else:
            print_error(f"{setting}: NOT FOUND")
            all_present = False
    
    return all_present


def test_smtp_connection(env_vars):
    """Test SMTP connection to Gmail"""
    print_header("STEP 2: TEST SMTP CONNECTION")
    
    email_host = env_vars.get('EMAIL_HOST', 'smtp.gmail.com')
    email_port = int(env_vars.get('EMAIL_PORT', '587'))
    email_use_tls = env_vars.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    email_timeout = int(env_vars.get('EMAIL_TIMEOUT', '10'))
    
    print(f"Connecting to: {email_host}:{email_port}")
    print(f"TLS: {email_use_tls}")
    print(f"Timeout: {email_timeout} seconds")
    
    try:
        print("\nAttempting connection...")
        server = smtplib.SMTP(
            host=email_host,
            port=email_port,
            timeout=email_timeout
        )
        print_success(f"Connected to {email_host}:{email_port}")
        
        # Start TLS
        if email_use_tls:
            print("\nStarting TLS encryption...")
            server.starttls()
            print_success("TLS enabled")
        
        return server
    
    except socket.gaierror as e:
        print_error(f"DNS Error: Cannot resolve '{email_host}'")
        print_info(f"Error details: {e}")
        print_info("Check: Internet connection and EMAIL_HOST setting")
        return None
    
    except socket.timeout as e:
        print_error(f"Connection timeout after {email_timeout} seconds")
        print_info(f"Error details: {e}")
        print_info("Check: Firewall and network connectivity")
        return None
    
    except ConnectionRefusedError as e:
        print_error(f"Connection refused by {email_host}:{email_port}")
        print_info(f"Error details: {e}")
        print_info("Check: Port number and firewall settings")
        return None
    
    except smtplib.SMTPException as e:
        print_error(f"SMTP Error: {type(e).__name__}")
        print_info(f"Error details: {e}")
        return None
    
    except Exception as e:
        print_error(f"Unexpected error: {type(e).__name__}")
        print_info(f"Error details: {e}")
        return None


def test_authentication(server, env_vars):
    """Test SMTP authentication"""
    print_header("STEP 3: TEST AUTHENTICATION")
    
    email_user = env_vars.get('EMAIL_HOST_USER', '')
    email_password = env_vars.get('EMAIL_HOST_PASSWORD', '')
    
    print(f"Email: {email_user}")
    
    try:
        print("\nAttempting authentication...")
        server.login(email_user, email_password)
        print_success(f"Successfully authenticated as {email_user}")
        return True
    
    except smtplib.SMTPAuthenticationError as e:
        print_error("Authentication failed!")
        print_info("Possible issues:")
        print_info("  1. Wrong email address (EMAIL_HOST_USER)")
        print_info("  2. Wrong password - using regular password instead of App Password?")
        print_info("  3. Gmail App Passwords not enabled")
        print_info("  4. Less secure app access disabled")
        print_info(f"\nError details: {e}")
        print_info("\nFix: Generate App Password at: https://myaccount.google.com/apppasswords")
        return False
    
    except Exception as e:
        print_error(f"Authentication error: {type(e).__name__}")
        print_info(f"Error details: {e}")
        return False


def send_test_email(server, env_vars):
    """Send a test email"""
    print_header("STEP 4: SEND TEST EMAIL")
    
    from_email = env_vars.get('DEFAULT_FROM_EMAIL', '')
    to_email = env_vars.get('ADMIN_EMAIL', '')
    
    print(f"From: {from_email}")
    print(f"To: {to_email}")
    
    # Create email
    message = MIMEMultipart('alternative')
    message['Subject'] = "🧪 VRL Logistics - Email System Test"
    message['From'] = from_email
    message['To'] = to_email
    
    # Plain text part
    text = f"""
Hello,

This is a test email from VRL Logistics email system.

If you received this, your email configuration is working correctly! ✅

═════════════════════════════════════════════════════════════
System Information:
  From: {from_email}
  Host: {env_vars.get('EMAIL_HOST')}
  Port: {env_vars.get('EMAIL_PORT')}
═════════════════════════════════════════════════════════════

Best regards,
VRL Logistics Email System

---
Do not reply to this email. This is an automated test message.
"""
    
    # HTML part
    html = f"""
<html>
  <head></head>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <h2>🧪 VRL Logistics - Email System Test</h2>
    <p>Hello,</p>
    <p>This is a <strong>test email</strong> from VRL Logistics email system.</p>
    <p style="font-size: 16px; color: #28a745;"><strong>If you received this, your email configuration is working correctly! ✅</strong></p>
    
    <hr style="border: none; border-top: 2px solid #ddd; margin: 20px 0;">
    
    <h3>System Information:</h3>
    <ul>
        <li><strong>From:</strong> {from_email}</li>
        <li><strong>Host:</strong> {env_vars.get('EMAIL_HOST')}</li>
        <li><strong>Port:</strong> {env_vars.get('EMAIL_PORT')}</li>
    </ul>
    
    <hr style="border: none; border-top: 2px solid #ddd; margin: 20px 0;">
    
    <p>Best regards,<br><strong>VRL Logistics Email System</strong></p>
    <p style="color: #999; font-size: 12px;">Do not reply to this email. This is an automated test message.</p>
  </body>
</html>
"""
    
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    message.attach(part1)
    message.attach(part2)
    
    try:
        print("\nSending test email...")
        server.send_message(message)
        print_success(f"Email sent to {to_email}")
        return True
    
    except Exception as e:
        print_error(f"Failed to send email: {type(e).__name__}")
        print_info(f"Error details: {e}")
        return False


def main():
    """Main verification flow"""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║  VRL LOGISTICS - EMAIL CONFIGURATION VERIFICATION                           ║")
    print("║  March 23, 2026                                                              ║")
    print("╚" + "=" * 78 + "╝")
    
    # Step 1: Load .env
    print("\nLoading .env file...")
    env_vars = load_env_file()
    if not env_vars:
        print_error("\nCannot proceed without .env file")
        sys.exit(1)
    
    # Step 2: Check configuration
    if not check_env_configuration(env_vars):
        print_error("\nMissing required settings in .env file")
        sys.exit(1)
    
    # Step 3: Test connection
    server = test_smtp_connection(env_vars)
    if not server:
        print_error("\nCannot connect to SMTP server")
        sys.exit(1)
    
    # Step 4: Test authentication
    if not test_authentication(server, env_vars):
        print_error("\nAuthentication failed")
        server.quit()
        sys.exit(1)
    
    # Step 5: Send test email
    success = send_test_email(server, env_vars)
    
    # Close connection
    server.quit()
    
    # Final report
    print_header("VERIFICATION SUMMARY")
    
    if success:
        print_success("All email tests passed! ✅")
        print("\n" + "=" * 80)
        print("Your email system is configured correctly.")
        print("Check the admin email inbox for the test message.")
        print("=" * 80 + "\n")
        sys.exit(0)
    else:
        print_error("Email verification failed. Check errors above.")
        print("\n" + "=" * 80)
        print("For help, see: EMAIL_CONFIGURATION_GUIDE.md")
        print("=" * 80 + "\n")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_error("\nVerification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
