import sys
import io
import os

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass


from extensions import db
from models.employee import Employee, EmailMessage
from services.ai_agent import extract_employee_info, generate_onboarding_response

from services.email_listener import get_all_emails
from services.email_service import send_email
from services.onboarding_service import get_missing_fields
from datetime import datetime

def poll_and_process_emails():
    print("[Inbox Poller] Fetching unread emails...")
    emails = get_all_emails()

    if not emails:
        print("[Inbox Poller] No new unread emails found.")
        return

    for sender, subject, body, message_id in emails:
        print(f"[Inbox Poller] Processing email from: {sender}")

        # Find employee
        emp = Employee.query.filter_by(email=sender).first()
        if not emp:
            print(f"[Inbox Poller] Sender '{sender}' is not a registered employee. Skipping.")
            continue

        print(f"[Inbox Poller] Found employee: {emp.name} (Status: {emp.status})")

        # 1. Log incoming email in database
        incoming_msg = EmailMessage(
            employee_id=emp.id,
            sender=sender,
            receiver=os.getenv("EMAIL_USER", "HR Agent"),
            subject=subject,
            body=body,
            message_id=message_id
        )
        db.session.add(incoming_msg)
        db.session.commit()

        # 2. Extract details using AI agent
        print("[Inbox Poller] Extracting details using AI Agent...")
        data = extract_employee_info(body)
        print(f"[Inbox Poller] Extracted data: {data}")

        if data.get("qualification"):
            emp.qualification = data["qualification"]
            print(f" -> Set Qualification: {emp.qualification}")

        if data.get("location"):
            emp.location = data["location"]
            print(f" -> Set Location: {emp.location}")

        if data.get("dob"):
            try:
                emp.dob = datetime.strptime(data["dob"], "%Y-%m-%d").date()
                print(f" -> Set Date of Birth: {emp.dob}")
            except Exception as e:
                print(f" -> Error parsing Date of Birth '{data['dob']}': {e}")

        # Update status to In Progress since we received a reply
        if emp.status == "Pending":
            emp.status = "In Progress"
        db.session.commit()

        # 3. Check for missing fields
        missing = get_missing_fields(emp)
        print(f"[Inbox Poller] Missing fields: {missing}")

        # 4. Generate reply using AI agent (passing employee, missing fields, and question)
        employee_question = data.get("employee_question")
        print(f"[Inbox Poller] Generating response. Question: {employee_question}")
        reply_body = generate_onboarding_response(emp, missing, employee_question)

        # 5. Determine subject & Send email
        reply_subject = subject
        if not reply_subject.lower().startswith("re:"):
            reply_subject = f"Re: {reply_subject}"

        # Send email and get outgoing message_id
        print(f"[Inbox Poller] Sending reply to: {emp.email}")
        outgoing_msg_id = send_email(
            emp.email,
            reply_subject,
            reply_body,
            in_reply_to=message_id,
            references=message_id
        )

        # Update employee status to Completed if no fields are missing
        if not missing:
            emp.status = "Completed"
            db.session.commit()
            print(f"[Inbox Poller] Onboarding completed for {emp.name}!")

        # 6. Log outgoing email in database
        outgoing_msg = EmailMessage(
            employee_id=emp.id,
            sender=os.getenv("EMAIL_USER", "HR Agent"),
            receiver=emp.email,
            subject=reply_subject,
            body=reply_body,
            message_id=outgoing_msg_id,
            in_reply_to=message_id
        )
        db.session.add(outgoing_msg)
        db.session.commit()

        print("[Inbox Poller] Email thread processed and logged successfully!")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        poll_and_process_emails()



        
