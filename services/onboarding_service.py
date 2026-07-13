def get_missing_fields(employee):
    missing = []

    if not employee.gender:
        missing.append("Gender")
    if not employee.dob:
        missing.append("Date of Birth")
    if not employee.mobile_number:
        missing.append("Mobile Number")
    if not employee.alternate_mobile:
        missing.append("Alternate Mobile Number")
    if not employee.marital_status:
        missing.append("Marital Status")
    if not employee.blood_group:
        missing.append("Blood Group")
    if not employee.branch_depot:
        missing.append("Employee Branch / Depot")
    if not employee.qualification:
        missing.append("Qualification")
    if not employee.location:
        missing.append("Location")

    return missing



def create_onboarding_email(employee):
    missing = get_missing_fields(employee)

    body = f"""Hi {employee.name},

Welcome to the company.

We still need the following information:

"""

    for field in missing:
        if field == "Date of Birth":
            body += f"- {field} (e.g., DD/MM/YYYY)\n"
        else:
            body += f"- {field}\n"

    body += """
Please reply directly to this email with your missing details.

Thank you,
HR Team
"""

    return body