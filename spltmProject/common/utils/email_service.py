"""
Email Service Module

This module provides a common function to send emails to participants
with support for HTML templates and plain text content.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Email Configuration
EMAIL_CONFIG = {
    "SmtpServer": "smtp.gmail.com",
    "SmtpPort": 587,
    "Username": "aniket.kum242@gmail.com",
    "Password": "lhhx dsxb domz zbuk",
    "DefaultFrom": "aniket.kum242@gmail.com"
}


def send_email(recipient_email, subject, body, is_html=False):
    """
    Send an email to a participant using Gmail SMTP.
    
    Args:
        recipient_email (str): Email address of the recipient
        subject (str): Email subject
        body (str): Email body (HTML if is_html=True, else plain text)
        is_html (bool): Whether the body is HTML or plain text
        
    Returns:
        dict: Status and message
        {
            "status": "success" or "error",
            "message": Description of the result,
            "email": recipient_email (if successful)
        }
        
    Example:
        # Send plain text OTP
        result = send_email(
            recipient_email="user@example.com",
            subject="Your OTP Code",
            body="Your OTP is: 123456. Valid for 10 minutes.",
            is_html=False
        )
        
        # Send HTML email
        result = send_email(
            recipient_email="user@example.com",
            subject="Your OTP Code",
            body="<h1>OTP</h1><p>Your OTP is: <b>123456</b></p>",
            is_html=True
        )
    """
    
    try:
        # Validate email
        if not recipient_email or '@' not in recipient_email:
            logger.error(f"Invalid email address: {recipient_email}")
            return {
                "status": "error",
                "message": "Invalid email address provided"
            }
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG['DefaultFrom']
        msg['To'] = recipient_email
        
        # Attach body
        if is_html:
            # Add plain text fallback for HTML emails
            plain_text = "If you cannot view this email, please use a text editor."
            msg.attach(MIMEText(plain_text, 'plain'))
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(EMAIL_CONFIG['SmtpServer'], EMAIL_CONFIG['SmtpPort'])
        server.starttls()  # Enable TLS encryption
        
        # Login to Gmail
        server.login(EMAIL_CONFIG['Username'], EMAIL_CONFIG['Password'])
        
        # Send email
        server.sendmail(
            from_addr=EMAIL_CONFIG['DefaultFrom'],
            to_addrs=[recipient_email],
            msg=msg.as_string()
        )
        
        # Close connection
        server.quit()
        
        logger.info(f"Email sent successfully to {recipient_email}")
        
        return {
            "status": "success",
            "message": f"Email sent successfully to {recipient_email}",
            "email": recipient_email
        }
        
    except smtplib.SMTPAuthenticationError:
        logger.error(f"SMTP Authentication failed for {EMAIL_CONFIG['Username']}")
        return {
            "status": "error",
            "message": "Email authentication failed. Check SMTP credentials."
        }
        
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {str(e)}")
        return {
            "status": "error",
            "message": f"SMTP error occurred: {str(e)}"
        }
        
    except Exception as e:
        logger.error(f"Unexpected error sending email to {recipient_email}: {str(e)}")
        return {
            "status": "error",
            "message": f"Error sending email: {str(e)}"
        }


def send_otp_email(email, otp, user_name=None):
    """
    Send OTP to user's email with formatted HTML template.
    
    Args:
        email (str): User's email address
        otp (str): 6-digit OTP code
        user_name (str, optional): User's name for personalization
        
    Returns:
        dict: Status and message
        
    Example:
        result = send_otp_email("user@example.com", "123456", "John Doe")
    """
    
    subject = "Your SplitMoney OTP Code"
    
    # Create HTML body
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #333;">Welcome to SplitMoney</h2>
                {f'<p>Hi {user_name},</p>' if user_name else '<p>Hello,</p>'}
                
                <p style="color: #666;">Your OTP (One-Time Password) for SplitMoney login is:</p>
                
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
                    SplitMoney Team<br>
                    © 2026 SplitMoney. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """
    
    # Send email
    result = send_email(
        recipient_email=email,
        subject=subject,
        body=html_body,
        is_html=True
    )
    
    return result


def send_event_invitation_email(email, event_name, event_date, event_details=None):
    """
    Send event invitation email to participant.
    
    Args:
        email (str): Participant's email address
        event_name (str): Name of the event
        event_date (str): Date of the event
        event_details (str, optional): Additional event details
        
    Returns:
        dict: Status and message
        
    Example:
        result = send_event_invitation_email(
            email="user@example.com",
            event_name="Team Dinner",
            event_date="2025-02-15",
            event_details="Downtown Restaurant"
        )
    """
    
    subject = f"You're invited to {event_name}"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #333;">Event Invitation</h2>
                
                <p style="color: #666;">You've been invited to an event on SplitMoney!</p>
                
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
                    SplitMoney Team<br>
                    © 2026 SplitMoney. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email(
        recipient_email=email,
        subject=subject,
        body=html_body,
        is_html=True
    )


def send_payment_reminder_email(email, event_name, amount_due, due_date=None):
    """
    Send payment reminder email to participant.
    
    Args:
        email (str): Participant's email address
        event_name (str): Name of the event
        amount_due (float): Amount to be paid
        due_date (str, optional): Payment due date
        
    Returns:
        dict: Status and message
        
    Example:
        result = send_payment_reminder_email(
            email="user@example.com",
            event_name="Team Dinner",
            amount_due=1500.00,
            due_date="2025-02-20"
        )
    """
    
    subject = f"Payment Reminder: {event_name}"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #333;">Payment Reminder</h2>
                
                <p style="color: #666;">This is a friendly reminder about a pending payment on SplitMoney.</p>
                
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
                    SplitMoney Team<br>
                    © 2026 SplitMoney. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email(
        recipient_email=email,
        subject=subject,
        body=html_body,
        is_html=True
    )
