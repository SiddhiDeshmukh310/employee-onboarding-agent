from app import app
from models.employee import Employee
from extensions import db
from services.ai_extractor import extract_details

text = """
My qualification is BE Computer Engineering.
I live in Pune.
My date of birth is 12 March 2003.
"""

data = extract_details(text)

with app.app_context():
    emp = Employee.query.filter_by(
        email="royal.rushi235@gmail.com"
    ).first()

    if emp:
        if data["qualification"]:
            emp.qualification = data["qualification"]

        if data["location"]:
            emp.location = data["location"]

        if data["dob"]:
            emp.dob = data["dob"]

        db.session.commit()

        print("Employee updated successfully!")
    else:
        print("Employee not found.")