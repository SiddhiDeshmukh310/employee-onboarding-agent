def get_missing_fields(employee):
    missing = []

    if not employee.qualification:
        missing.append("Qualification")

    if not employee.dob:
        missing.append("Date of Birth")

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
        body += f"- {field}\n"

    body += """
Please reply directly to this email with your missing details.

Thank you,
HR Team
"""

    return body