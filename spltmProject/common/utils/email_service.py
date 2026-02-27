"""
Email Service Module

Working production-safe SMTP version
Supports SSL (465) and TLS (587)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# -------------------------------------------------------
# Email Configuration
# -------------------------------------------------------
EMAIL_CONFIG = {
    "SmtpServer": "mail.evenpay.in",
    "SmtpPort": 465,  # 465 = SSL | 587 = TLS
    "Username": "noreply@evenpay.in",
    "Password": "MaCNCut~bVlnG+k6",
    "DefaultFrom": "noreply@evenpay.in",
}


# -------------------------------------------------------
# COMMON EMAIL FUNCTION
# -------------------------------------------------------
def send_email(recipient_email, subject, body, is_html=False):

    def mask_password(pwd):
        if not pwd:
            return "NOT SET"
        pwd = str(pwd)
        if len(pwd) <= 4:
            return "*" * len(pwd)
        return "*" * (len(pwd) - 4) + pwd[-4:]

    server = None

    try:
        # Validate email
        if not recipient_email or '@' not in recipient_email:
            logger.error(f"Invalid email address: {recipient_email}")
            return {
                "status": "error",
                "email_message": "Invalid email address provided"
            }

        # Debug info
        print("SMTP DEBUG INFO")
        print(f"Server   : {EMAIL_CONFIG['SmtpServer']}")
        print(f"Port     : {EMAIL_CONFIG['SmtpPort']}")
        print(f"Username : {EMAIL_CONFIG['Username']}")
        print(f"Password : {mask_password(EMAIL_CONFIG['Password'])}")

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG['DefaultFrom']
        msg['To'] = recipient_email

        if is_html:
            msg.attach(MIMEText("Please view this email in HTML format.", 'plain'))
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # -------------------------------------------------------
        # SMTP CONNECTION (AUTO SSL/TLS)
        # -------------------------------------------------------
        port = EMAIL_CONFIG["SmtpPort"]

        if port == 465:
            # SSL
            server = smtplib.SMTP_SSL(
                EMAIL_CONFIG["SmtpServer"],
                port,
                timeout=30
            )
            server.ehlo()
        else:
            # TLS
            server = smtplib.SMTP(
                EMAIL_CONFIG["SmtpServer"],
                port,
                timeout=30
            )
            server.ehlo()
            server.starttls()
            server.ehlo()

        # Login
        server.login(
            EMAIL_CONFIG["Username"],
            EMAIL_CONFIG["Password"]
        )

        # Send email
        server.sendmail(
            from_addr=EMAIL_CONFIG["DefaultFrom"],
            to_addrs=[recipient_email],
            msg=msg.as_string()
        )

        logger.info(f"Email sent successfully to {recipient_email}")

        return {
            "status": "success",
            "email_message": f"Email sent successfully to {recipient_email}",
            "email": recipient_email
        }

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed | Error={str(e)}")
        return {
            "status": "error",
            "email_message": "Email authentication failed"
        }

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error | Error={str(e)}")
        return {
            "status": "error",
            "email_message": f"SMTP error occurred: {str(e)}"
        }

    except Exception as e:
        logger.error(f"Unexpected error | Error={str(e)}")
        return {
            "status": "error",
            "email_message": f"Unexpected error: {str(e)}"
        }

    finally:
        if server:
            try:
                server.quit()
            except:
                pass


# -------------------------------------------------------
# OTP EMAIL
# -------------------------------------------------------
def send_otp_email(email, otp, user_name=None):

    subject = "Your EvenPay OTP Code"

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #333;">Welcome to EvenPay</h2>
                {f'<p>Hi {user_name},</p>' if user_name else '<p>Hello,</p>'}
                
                <p style="color: #666;">Your OTP (One-Time Password) for EvenPay login is:</p>
                
                <div style="background-color: #007bff; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <h1 style="letter-spacing: 5px; margin: 0;">{otp}</h1>
                </div>
                
                <p style="color: #666;">
                    <strong>Important:</strong> This OTP is valid for <strong>10 minutes</strong> only.
                    Do not share this code with anyone.
                </p>
                
                <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                    If you didn't request this OTP, please ignore this email or contact support.
                </p>
                
                <p style="color: #999; font-size: 12px; margin-top: 10px;">
                    EvenPay Team<br>
                    © 2026 EvenPay. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """

    return send_email(email, subject, html_body, True)


# -------------------------------------------------------
# EVENT INVITATION EMAIL
# -------------------------------------------------------
def send_event_invitation_email(email, event_name, event_date, event_details=None):

    subject = f"You're invited to {event_name}"

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #333;">Event Invitation</h2>
                
                <p style="color: #666;">You've been invited to an event on EvenPay!</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #007bff; margin: 20px 0;">
                    <h3 style="color: #007bff; margin-top: 0;">{event_name}</h3>
                    <p style="margin: 10px 0;"><strong>Date:</strong> {event_date}</p>
                    {f'<p style="margin: 10px 0;"><strong>Details:</strong> {event_details}</p>' if event_details else ''}
                </div>
                
                <p style="color: #666;">Click the link below to view and manage the event:</p>
                <p style="margin-top: 30px;">
                    <a href="http://localhost:8000/dashboard/" style="display: inline-block; padding: 12px 30px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px;">View Event</a>
                </p>
                
                <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                    EvenPay Team<br>
                    © 2026 EvenPay. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """

    return send_email(email, subject, html_body, True)


# -------------------------------------------------------
# PAYMENT REMINDER EMAIL
# -------------------------------------------------------
def send_payment_reminder_email(email, event_name, amount_due, due_date=None):

    subject = f"Payment Reminder: {event_name}"

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #333;">Payment Reminder</h2>
                
                <p style="color: #666;">This is a friendly reminder about a pending payment on EvenPay.</p>
                
                <div style="background-color: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <h3 style="color: #856404; margin-top: 0;">{event_name}</h3>
                    <p style="margin: 10px 0;"><strong>Amount Due:</strong> ₹{amount_due:.2f}</p>
                    {f'<p style="margin: 10px 0;"><strong>Due Date:</strong> {due_date}</p>' if due_date else ''}
                </div>
                
                <p style="color: #666;">Please complete your payment at your earliest convenience.</p>
                
                <p style="margin-top: 30px;">
                    <a href="http://localhost:8000/dashboard/" style="display: inline-block; padding: 12px 30px; background-color: #ffc107; color: #333; text-decoration: none; border-radius: 4px;">Make Payment</a>
                </p>
                
                <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                    EvenPay Team<br>
                    © 2026 EvenPay. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """

    return send_email(email, subject, html_body, True)