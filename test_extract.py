from services.ai_extractor import extract_details

text = """
My qualification is BE Computer Engineering.
I live in Pune.
My date of birth is 12 March 2003.
"""

print(extract_details(text))