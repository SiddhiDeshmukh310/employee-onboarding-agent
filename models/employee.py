from extensions import db

class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    qualification = db.Column(db.String(200))
    dob = db.Column(db.Date)
    location = db.Column(db.String(100))
    status = db.Column(db.String(50), default="Pending")

class EmailMessage(db.Model):
    __tablename__ = "email_messages"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    receiver = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    message_id = db.Column(db.String(255))
    in_reply_to = db.Column(db.String(255))

    employee = db.relationship("Employee", backref=db.backref("emails", lazy=True, cascade="all, delete-orphan"))