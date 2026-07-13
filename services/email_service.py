import smtplib
from email.mime.text import MIMEText
import os
import email.utils
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_email(to_email, subject, body, in_reply_to=None, references=None):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to_email

    # Generate a unique Message-ID
    msg_id = email.utils.make_msgid(domain=EMAIL.split('@')[-1] if EMAIL else 'gmail.com')
    msg["Message-ID"] = msg_id

    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)

    return msg_id