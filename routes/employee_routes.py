from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.employee import Employee, EmailMessage
from services.email_service import send_email
from services.onboarding_service import create_onboarding_email, get_missing_fields
from process_inbox import poll_and_process_emails
from datetime import datetime
import os


employee_bp = Blueprint('employee', __name__)

@employee_bp.route("/")
@employee_bp.route("/employees")
def employees():
    import traceback
    try:
        all_employees = Employee.query.all()
        
        # Calculate stats
        total = len(all_employees)
        completed = len([e for e in all_employees if e.status == "Completed"])
        in_progress = len([e for e in all_employees if e.status == "In Progress"])
        pending = len([e for e in all_employees if e.status == "Pending"])
        
        # Enrich employees with progress percentage and missing fields list
        enriched = []
        for emp in all_employees:
            missing = get_missing_fields(emp)
            # Total fields: Name, Qualification, DOB, Location
            # Name is mandatory at entry, so 1/4 fields is 25% complete.
            filled_count = 4 - len(missing)
            pct = int((filled_count / 4.0) * 100)
            
            enriched.append({
                "id": emp.id,
                "name": emp.name,
                "first_name": emp.first_name or emp.name,
                "email": emp.email,
                "mobile_number": emp.mobile_number or "-",
                "branch_depot": emp.branch_depot or "-",
                "qualification": emp.qualification or "-",
                "dob": emp.dob.strftime("%Y-%m-%d") if emp.dob else "-",
                "location": emp.location or "-",
                "status": emp.status,
                "progress": pct,
                "missing": ", ".join(missing) if missing else "None"
            })
            
        return render_template(
            "employees.html",
            employees=enriched,
            stats={
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "pending": pending
            }
        )
    except Exception as e:
        return f"<pre>Error Loading Dashboard:\n{traceback.format_exc()}</pre>", 500


@employee_bp.route("/add", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        first_name = request.form["first_name"]
        middle_name = request.form.get("middle_name") or ""
        last_name = request.form.get("last_name") or ""
        gender = request.form.get("gender") or ""
        email_addr = request.form["email"]
        mobile_number = request.form.get("mobile_number") or ""
        alternate_mobile = request.form.get("alternate_mobile") or ""
        marital_status = request.form.get("marital_status") or ""
        blood_group = request.form.get("blood_group") or ""
        branch_depot = request.form.get("branch_depot") or ""

        # Check if email already exists
        exists = Employee.query.filter_by(email=email_addr).first()
        if exists:
            return render_template("add_employee.html", error="Employee with this email already exists.")

        dob_val = None
        dob_input = request.form.get("dob")
        if dob_input:
            try:
                dob_val = datetime.strptime(dob_input, "%Y-%m-%d").date()
            except:
                try:
                    dob_val = datetime.strptime(dob_input, "%d-%m-%Y").date()
                except:
                    pass

        emp = Employee(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            gender=gender,
            name=f"{first_name} {middle_name or ''} {last_name or ''}".strip(),
            email=email_addr,
            dob=dob_val,
            mobile_number=mobile_number,
            alternate_mobile=alternate_mobile,
            marital_status=marital_status,
            blood_group=blood_group,
            branch_depot=branch_depot,
            status="Pending"
        )

        db.session.add(emp)
        db.session.commit()
        
        # Initiate onboarding email
        body = create_onboarding_email(emp)
        
        try:
            msg_id = send_email(emp.email, f"Onboarding Invitation - Action Required: {emp.name}", body)
            # Log outgoing invitation in the email_messages table
            invitation_msg = EmailMessage(
                employee_id=emp.id,
                sender=os.getenv("EMAIL_USER", "HR Agent"),
                receiver=emp.email,
                subject=f"Onboarding Invitation - Action Required: {emp.name}",
                body=body,
                message_id=msg_id
            )
            db.session.add(invitation_msg)
            db.session.commit()
        except Exception as e:
            print(f"Error sending/logging initial email: {e}")

        return redirect(url_for("employee.employees"))

    return render_template("add_employee.html")

@employee_bp.route("/edit/<int:emp_id>", methods=["GET", "POST"])
def edit_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    
    if request.method == "POST":
        emp.first_name = request.form["first_name"]
        emp.middle_name = request.form.get("middle_name") or ""
        emp.last_name = request.form.get("last_name") or ""
        emp.gender = request.form.get("gender") or ""
        emp.email = request.form["email"]
        emp.name = f"{emp.first_name} {emp.middle_name or ''} {emp.last_name or ''}".strip()
        emp.qualification = request.form.get("qualification") or None
        
        dob_val = request.form.get("dob")
        if dob_val:
            try:
                emp.dob = datetime.strptime(dob_val, "%Y-%m-%d").date()
            except:
                try:
                    emp.dob = datetime.strptime(dob_val, "%d-%m-%Y").date()
                except:
                    pass
        else:
            emp.dob = None
            
        emp.mobile_number = request.form.get("mobile_number") or ""
        emp.alternate_mobile = request.form.get("alternate_mobile") or ""
        emp.marital_status = request.form.get("marital_status") or ""
        emp.blood_group = request.form.get("blood_group") or ""
        emp.branch_depot = request.form.get("branch_depot") or ""
        emp.location = request.form.get("location") or None
        
        # Recheck status based on fields
        missing = get_missing_fields(emp)
        if not missing:
            emp.status = "Completed"
        elif emp.qualification or emp.dob or emp.location:
            emp.status = "In Progress"
        else:
            emp.status = "Pending"
            
        db.session.commit()
        return redirect(url_for("employee.employees"))
        
    dob_str = emp.dob.strftime("%Y-%m-%d") if emp.dob else ""
    return render_template("edit_employee.html", employee=emp, dob_str=dob_str)

@employee_bp.route("/delete/<int:emp_id>")
def delete_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    db.session.delete(emp)
    db.session.commit()
    return redirect(url_for("employee.employees"))

@employee_bp.route("/employee/<int:emp_id>/thread")
def view_thread(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    messages = EmailMessage.query.filter_by(employee_id=emp.id).order_by(EmailMessage.timestamp.asc()).all()
    missing = get_missing_fields(emp)
    
    # Format message objects
    formatted_msgs = []
    for msg in messages:
        formatted_msgs.append({
            "sender": msg.sender,
            "receiver": msg.receiver,
            "subject": msg.subject,
            "body": msg.body.replace("\n", "<br>"),
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "is_agent": "HR" in msg.sender or "@company.com" in msg.sender or msg.sender != emp.email
        })
        
    return render_template("thread.html", employee=emp, messages=formatted_msgs, missing=missing)

@employee_bp.route("/sync")
def sync():
    print("[Manual Sync] Triggering inbox check...")
    poll_and_process_emails()
    return redirect(url_for("employee.employees"))

@employee_bp.route("/employee/<int:emp_id>/simulate-reply", methods=["POST"])
def simulate_reply(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    body_text = request.form["body"]
    
    # 1. Log simulated incoming email in the database
    import email.utils
    simulated_msg_id = email.utils.make_msgid(domain="simulated.candidate.com")
    
    incoming_msg = EmailMessage(
        employee_id=emp.id,
        sender=emp.email,
        receiver=os.getenv("EMAIL_USER", "HR Agent"),
        subject=f"Re: Onboarding Invitation - Action Required: {emp.name}",
        body=body_text,
        message_id=simulated_msg_id
    )
    db.session.add(incoming_msg)
    db.session.commit()
    
    # 2. Extract details using AI agent
    from services.ai_agent import extract_employee_info, generate_onboarding_response
    from services.onboarding_service import get_missing_fields
    
    data = extract_employee_info(body_text)
    
    if data.get("qualification"):
        emp.qualification = data["qualification"]
    if data.get("location"):
        emp.location = data["location"]
    if data.get("dob"):
        try:
            emp.dob = datetime.strptime(data["dob"], "%Y-%m-%d").date()
        except:
            pass
    if data.get("gender"):
        emp.gender = data["gender"]
    if data.get("mobile_number"):
        emp.mobile_number = data["mobile_number"]
    if data.get("alternate_mobile"):
        emp.alternate_mobile = data["alternate_mobile"]
    if data.get("marital_status"):
        emp.marital_status = data["marital_status"]
    if data.get("blood_group"):
        emp.blood_group = data["blood_group"]
    if data.get("branch_depot"):
        emp.branch_depot = data["branch_depot"]

            
    if emp.status == "Pending":
        emp.status = "In Progress"
    db.session.commit()
    
    # 3. Check for missing fields
    missing = get_missing_fields(emp)
    
    # 4. Generate AI response
    employee_question = data.get("employee_question")
    reply_body = generate_onboarding_response(emp, missing, employee_question)
    
    # 5. Send actual email response back to candidate's real email address
    reply_subject = f"Re: Onboarding Invitation - Action Required: {emp.name}"
    outgoing_msg_id = send_email(
        emp.email,
        reply_subject,
        reply_body,
        in_reply_to=simulated_msg_id,
        references=simulated_msg_id
    )
    
    if not missing:
        emp.status = "Completed"
        db.session.commit()
        
    # 6. Log outgoing email in the database
    outgoing_msg = EmailMessage(
        employee_id=emp.id,
        sender=os.getenv("EMAIL_USER", "HR Agent"),
        receiver=emp.email,
        subject=reply_subject,
        body=reply_body,
        message_id=outgoing_msg_id,
        in_reply_to=simulated_msg_id
    )
    db.session.add(outgoing_msg)
    db.session.commit()
    
    return redirect(url_for("employee.view_thread", emp_id=emp.id))

@employee_bp.route("/employee/<int:emp_id>/view")
def view_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    dob_str = emp.dob.strftime("%d-%m-%Y") if emp.dob else "-"
    return render_template("view_employee.html", employee=emp, dob_str=dob_str)

@employee_bp.route("/init-db")
def init_db():
    print("[DB Init] Dropping all tables...")
    db.drop_all()
    print("[DB Init] Creating all tables...")
    db.create_all()
    print("[DB Init] Database initialized successfully!")
    return "Database initialized successfully! Go back to <a href='/'>Dashboard</a>."

