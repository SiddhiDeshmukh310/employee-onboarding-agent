from services.ai_agent import extract_employee_info

text = """
Hi,

I completed my BE in Computer Engineering.
I live in Pune.

What documents do I need to bring?
"""

print(extract_employee_info(text))