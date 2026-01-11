"""Email service using SMTP for Splitwiser (supports Gmail, Brevo, etc.)"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Environment configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")  # SMTP login username
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # SMTP login password
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_EMAIL)  # Sender email (can be different for services like Brevo)
FROM_NAME = os.getenv("FROM_NAME", "Splitwiser")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def is_email_configured() -> bool:
    """Check if email service is properly configured"""
    return bool(SMTP_EMAIL and SMTP_PASSWORD and FROM_EMAIL)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str
) -> bool:
    """
    Send an email via SMTP

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML version of email body
        text_content: Plain text version of email body

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not is_email_configured():
        logger.error("Email service not configured: SMTP_EMAIL, SMTP_PASSWORD, and FROM_EMAIL required")
        return False

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        message["To"] = to_email

        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)

        # Connect to SMTP server and send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # Upgrade to secure connection
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(message)

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed - check email credentials")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        return False


async def send_password_reset_email(
    user_email: str,
    user_name: str,
    reset_token: str
) -> bool:
    """
    Send password reset email with reset link

    Args:
        user_email: User's email address
        user_name: User's full name
        reset_token: Password reset token (not hashed)

    Returns:
        bool: True if email sent successfully
    """
    reset_link = f"{FRONTEND_URL}/reset-password/{reset_token}"

    subject = "Reset Your Splitwiser Password"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p>We received a request to reset your password for your Splitwiser account.</p>
                <p>Click the button below to reset your password:</p>
                <p style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Password</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #4F46E5;">{reset_link}</p>
                <p><strong>This link will expire in 1 hour.</strong></p>
                <p>If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.</p>
            </div>
            <div class="footer">
                <p>This is an automated message from Splitwiser. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
Hi {user_name},

We received a request to reset your password for your Splitwiser account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.

---
This is an automated message from Splitwiser.
    """

    return await send_email(user_email, subject, html_content, text_content)


async def send_email_verification_email(
    user_email: str,
    user_name: str,
    new_email: str,
    verification_token: str
) -> bool:
    """
    Send email verification link to new email address

    Args:
        user_email: User's current email (not used, but kept for consistency)
        user_name: User's full name
        new_email: New email address to verify
        verification_token: Email verification token (not hashed)

    Returns:
        bool: True if email sent successfully
    """
    verification_link = f"{FRONTEND_URL}/verify-email/{verification_token}"

    subject = "Verify Your New Email Address - Splitwiser"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Verify Your Email Address</h1>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p>Please verify your new email address for your Splitwiser account.</p>
                <p>Click the button below to verify this email address:</p>
                <p style="text-align: center;">
                    <a href="{verification_link}" class="button">Verify Email</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #4F46E5;">{verification_link}</p>
                <p><strong>This link will expire in 24 hours.</strong></p>
                <p>If you didn't request this email change, please contact support immediately.</p>
            </div>
            <div class="footer">
                <p>This is an automated message from Splitwiser. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
Hi {user_name},

Please verify your new email address for your Splitwiser account.

Click the link below to verify this email address:
{verification_link}

This link will expire in 24 hours.

If you didn't request this email change, please contact support immediately.

---
This is an automated message from Splitwiser.
    """

    return await send_email(new_email, subject, html_content, text_content)


async def send_email_change_notification(
    old_email: str,
    user_name: str,
    new_email: str
) -> bool:
    """
    Send notification to old email that address was changed

    Args:
        old_email: User's old email address
        user_name: User's full name
        new_email: New email address (partially masked for security)

    Returns:
        bool: True if email sent successfully
    """
    # Mask the new email for security
    new_email_parts = new_email.split('@')
    if len(new_email_parts) == 2:
        masked_email = new_email_parts[0][:2] + "***@" + new_email_parts[1]
    else:
        masked_email = "***"

    subject = "Your Splitwiser Email Address Has Been Changed"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #EF4444; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .warning {{ background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 10px; margin: 20px 0; }}
            .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Security Alert</h1>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p>This is a security notification that the email address for your Splitwiser account has been changed.</p>
                <div class="warning">
                    <strong>New email address:</strong> {masked_email}
                </div>
                <p>If you made this change, you can safely ignore this email.</p>
                <p><strong>If you did NOT make this change:</strong></p>
                <ul>
                    <li>Your account may have been compromised</li>
                    <li>Contact support immediately</li>
                    <li>Change your password on all accounts that share the same password</li>
                </ul>
            </div>
            <div class="footer">
                <p>This is an automated security message from Splitwiser. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
Hi {user_name},

SECURITY ALERT

This is a security notification that the email address for your Splitwiser account has been changed.

New email address: {masked_email}

If you made this change, you can safely ignore this email.

If you did NOT make this change:
- Your account may have been compromised
- Contact support immediately
- Change your password on all accounts that share the same password

---
This is an automated security message from Splitwiser.
    """

    return await send_email(old_email, subject, html_content, text_content)


async def send_password_changed_notification(
    user_email: str,
    user_name: str
) -> bool:
    """
    Send notification that password was changed

    Args:
        user_email: User's email address
        user_name: User's full name

    Returns:
        bool: True if email sent successfully
    """
    subject = "Your Splitwiser Password Has Been Changed"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #10B981; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .info {{ background-color: #F0FDF4; border-left: 4px solid #10B981; padding: 10px; margin: 20px 0; }}
            .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Changed Successfully</h1>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p>This is a confirmation that your Splitwiser account password has been changed successfully.</p>
                <div class="info">
                    <p>For your security, you have been logged out of all other devices.</p>
                </div>
                <p>If you made this change, you can safely ignore this email.</p>
                <p><strong>If you did NOT make this change:</strong></p>
                <ul>
                    <li>Your account may have been compromised</li>
                    <li>Contact support immediately</li>
                    <li>Use the "Forgot Password" feature to reset your password</li>
                </ul>
            </div>
            <div class="footer">
                <p>This is an automated security message from Splitwiser. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
Hi {user_name},

This is a confirmation that your Splitwiser account password has been changed successfully.

For your security, you have been logged out of all other devices.

If you made this change, you can safely ignore this email.

If you did NOT make this change:
- Your account may have been compromised
- Contact support immediately
- Use the "Forgot Password" feature to reset your password

---
This is an automated security message from Splitwiser.
    """

    return await send_email(user_email, subject, html_content, text_content)
