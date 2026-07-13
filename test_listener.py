import imaplib
import email
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASSWORD")

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(EMAIL, PASSWORD)
mail.select("inbox")

status, messages = mail.search(None, "ALL")
print("Email IDs:", messages)

email_ids = messages[0].split()[-20:][-20:][-20:]

for e_id in email_ids[-5:]:  # last 5 emails
    status, msg_data = mail.fetch(e_id, "(RFC822)")

    for response in msg_data:
        if isinstance(response, tuple):
            msg = email.message_from_bytes(response[1])

            print("\n====================")
            print("From:", msg["From"])
            print("Subject:", msg["Subject"])

            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(errors="ignore")
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors="ignore")

            print("Body:")
            print(body)

mail.logout()