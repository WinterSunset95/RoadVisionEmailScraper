from dotenv import load_dotenv
from bs4 import BeautifulSoup
import smtplib
import os
# 🚀 Use the modern, simpler EmailMessage class
from email.message import EmailMessage

load_dotenv()

# --- Configuration ---
# Your environment variable setup is excellent!
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or ""
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD") or ""
SMTP_SERVER = os.getenv("SMTP_SERVER") or ""
SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL") or ""
SUBJECT = "Daily Tenders"

def send_html_email(soup: BeautifulSoup):
    """
    Constructs an email from a BeautifulSoup object and sends it using Gmail's SMTP server.
    """
    if not SENDER_EMAIL or not SENDER_APP_PASSWORD:
        print("❌ Error: SENDER_EMAIL or SENDER_APP_PASSWORD environment variables not set.")
        return
    if not RECEIVER_EMAIL:
        print("❌ Error: RECEIVER_EMAIL environment variable not set.")
        return 
    if not SMTP_SERVER or not SMTP_PORT:
        print("❌ Error: SMTP_SERVER or SMTP_PORT environment variables not set.")
        return

    print(f"Preparing to send email from {SENDER_EMAIL} to {RECEIVER_EMAIL}...")
    
    # --- Step 1: Construct the email message using EmailMessage ---
    message = EmailMessage()
    message["Subject"] = SUBJECT
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL

    # ✅ This is the simpler way to set the HTML content.
    # We use str(soup) instead of soup.prettify() to avoid extra whitespace
    # that can sometimes affect rendering in email clients.
    message.set_content(str(soup), subtype='html')
    
    # --- Step 2: Connect to the SMTP server and send ---
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.send_message(message) # .send_message() is the modern method for this object
        
        print(f"🎉 Email sent successfully to {RECEIVER_EMAIL}!")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
