#!/usr/bin/env python3
"""
Test email configuration for Splitwiser
Usage: python test_email_config.py
"""

import os
import sys
import asyncio

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.email import (
    is_email_configured,
    send_email,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_EMAIL,
    FROM_EMAIL,
    FROM_NAME,
    FRONTEND_URL
)


def print_config():
    """Print current email configuration"""
    print("=" * 60)
    print("EMAIL CONFIGURATION")
    print("=" * 60)
    print(f"SMTP_HOST:     {SMTP_HOST}")
    print(f"SMTP_PORT:     {SMTP_PORT}")
    print(f"SMTP_EMAIL:    {SMTP_EMAIL or '❌ NOT SET'}")
    print(f"SMTP_PASSWORD: {'✓ SET' if os.getenv('SMTP_PASSWORD') else '❌ NOT SET'}")
    print(f"FROM_EMAIL:    {FROM_EMAIL or '❌ NOT SET'}")
    print(f"FROM_NAME:     {FROM_NAME}")
    print(f"FRONTEND_URL:  {FRONTEND_URL}")
    print()
    print(f"Status: {'✓ CONFIGURED' if is_email_configured() else '❌ NOT CONFIGURED'}")
    print("=" * 60)


async def test_email(recipient: str):
    """Send a test email"""
    print(f"\nSending test email to {recipient}...")

    subject = "Test Email from Splitwiser"

    html_content = """
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #4F46E5;">Test Email</h2>
        <p>This is a test email from your Splitwiser application.</p>
        <p>If you received this, your email configuration is working correctly! ✓</p>
        <hr>
        <p style="font-size: 12px; color: #666;">
            Sent from Splitwiser email service
        </p>
    </body>
    </html>
    """

    text_content = """
Test Email from Splitwiser

This is a test email from your Splitwiser application.

If you received this, your email configuration is working correctly! ✓

---
Sent from Splitwiser email service
    """

    success = await send_email(recipient, subject, html_content, text_content)

    if success:
        print("✓ Email sent successfully!")
        print(f"  Check {recipient} for the test email.")
    else:
        print("❌ Failed to send email.")
        print("  Check the logs above for error details.")

    return success


async def main():
    """Main test function"""
    print()
    print_config()

    if not is_email_configured():
        print("\n❌ Email service is not configured.")
        print("\nTo configure, set these environment variables:")
        print("  export SMTP_HOST=smtp-relay.brevo.com")
        print("  export SMTP_PORT=587")
        print("  export SMTP_EMAIL=9fc28f001@smtp-brevo.com")
        print("  export SMTP_PASSWORD=<your-brevo-smtp-key>")
        print("  export FROM_EMAIL=<your-verified-sender-email>")
        print("  export FROM_NAME=Splitwiser")
        print()
        return

    # Prompt for test email
    print()
    recipient = input("Enter email address to send test email to: ").strip()

    if not recipient or '@' not in recipient:
        print("❌ Invalid email address")
        return

    print()
    await test_email(recipient)
    print()


if __name__ == "__main__":
    asyncio.run(main())
