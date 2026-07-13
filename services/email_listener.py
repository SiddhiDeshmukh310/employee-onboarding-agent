import imaplib
import email
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASSWORD")


def get_all_emails():
    if not EMAIL or not PASSWORD:
        print("[Email Listener] Credentials not configured. Skipping IMAP check.")
        return []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        # Search for UNSEEN emails
        status, messages = mail.search(None, "UNSEEN")
        if not messages[0]:
            mail.logout()
            return []

        email_ids = messages[0].split()
        emails = []

        for e_id in reversed(email_ids):
            status, msg_data = mail.fetch(e_id, "(RFC822)")

            for response in msg_data:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])

                    sender = email.utils.parseaddr(
                        msg["From"]
                    )[1]

                    subject = msg["Subject"]
                    message_id = msg["Message-ID"]

                    body = ""

                    if msg.is_multipart():
                        for part in msg.walk():
                            if (
                                part.get_content_type()
                                == "text/plain"
                            ):
                                payload = part.get_payload(
                                    decode=True
                                )

                                if payload:
                                    body = payload.decode(
                                        errors="ignore"
                                    )
                                    break
                    else:
                        payload = msg.get_payload(
                            decode=True
                        )

                        if payload:
                            body = payload.decode(
                                errors="ignore"
                            )

                    emails.append(
                        (sender, subject, body, message_id)
                    )

        mail.logout()
        return emails
    except Exception as e:
        print(f"[Email Listener] IMAP Error: {e}")
        return []