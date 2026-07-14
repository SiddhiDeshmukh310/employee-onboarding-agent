import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from services.knowledge_base import get_kb_context, search_kb_fallback

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    # Use gemini-3.5-flash which is the active preview model
    model = genai.GenerativeModel("gemini-3.5-flash")
else:
    model = None

def clean_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

import re

def strip_quoted_text(text):
    if not text:
        return ""
    # Split by common headers indicating quoted reply history
    # 1. "On ... wrote:"
    text = re.split(r'On\s+[A-Za-z0-9,:\s\-\+\#\.\/]+\s+wrote:', text, flags=re.IGNORECASE)[0]
    # 2. "-----Original Message-----"
    text = re.split(r'-----Original Message-----', text, flags=re.IGNORECASE)[0]
    # 3. "From:" (common in forward/reply chains)
    text = re.split(r'From\:\s+', text, flags=re.IGNORECASE)[0]
    # 4. Remove lines starting with ">"
    lines = text.split('\n')
    clean_lines = [line for line in lines if not line.strip().startswith('>')]
    return '\n'.join(clean_lines).strip()

def extract_employee_info(email_text):
    email_text = strip_quoted_text(email_text)
    if not model:
        print("[AI Agent] No Gemini API key configured. Using local fallback extraction.")
        return extract_employee_info_fallback(email_text)


    prompt = f"""
    You are an HR onboarding AI.
    Extract the following information from the email text:
    - qualification
    - dob (Format strictly as YYYY-MM-DD. Extract date of birth if mentioned in any format like '12 March 2003' or '12-03-2003' or 'May 12 1996')
    - location
    - gender (Male, Female, or Other)
    - mobile_number
    - alternate_mobile
    - marital_status (Single, Married, Divorced, or Widow)
    - blood_group (A+, A-, B+, B-, AB+, AB-, O+, O-)
    - branch_depot (Any branch/depot details mentioned, e.g., Bhekarainagar or Central Workshop)
    - employee_question (Any question the employee is asking. If none, write null)

    Return ONLY a valid JSON object. Do not wrap in markdown or code blocks.
    
    Example:
    {{
        "qualification": "BE Computer Engineering",
        "dob": "2003-03-12",
        "location": "Pune",
        "gender": "Male",
        "mobile_number": "7970970970",
        "alternate_mobile": "7090909997",
        "marital_status": "Married",
        "blood_group": "A+",
        "branch_depot": "Bhekarainagar",
        "employee_question": "What documents are required for joining?"
    }}

    Email text:
    {email_text}
    """

    try:
        response = model.generate_content(prompt)
        cleaned = clean_json_response(response.text)
        return json.loads(cleaned)
    except Exception as e:
        print(f"[AI Agent] Gemini extraction failed: {e}. Falling back to local parser.")
        return extract_employee_info_fallback(email_text)

def extract_employee_info_fallback(email_text):
    from services.ai_extractor import extract_details
    details = extract_details(email_text)
    
    # Simple check for employee questions
    question = None
    email_lower = email_text.lower()
    
    # Only detect a question if the email contains a question mark or a question phrase
    has_question = '?' in email_text or any(q in email_lower for q in ['what is', 'what are', 'when is', 'where is', 'how to', 'which documents', 'dress code'])
    
    if has_question:
        question_triggers = ["documents", "docs", "joining details", "dress", "timings", "hybrid", "working hours", "where", "location", "address", "metro"]
        for trigger in question_triggers:
            if trigger in email_lower:
                question = f"What are the details regarding {trigger}?"
                break

            
    # Format dob to string if it was parsed as date
    dob_str = None
    if details.get("dob"):
        try:
            if isinstance(details["dob"], str):
                dob_str = details["dob"]
            else:
                dob_str = details["dob"].strftime("%Y-%m-%d")
        except:
            dob_str = str(details["dob"])

    return {
        "qualification": details.get("qualification"),
        "dob": dob_str,
        "location": details.get("location"),
        "gender": details.get("gender"),
        "mobile_number": details.get("mobile_number"),
        "alternate_mobile": details.get("alternate_mobile"),
        "marital_status": details.get("marital_status"),
        "blood_group": details.get("blood_group"),
        "branch_depot": details.get("branch_depot"),
        "employee_question": question
    }


def generate_onboarding_response(employee, missing_fields, employee_question):
    if not missing_fields and not employee_question:
        return f"""Hi {employee.name},

Your onboarding completion is done. We look forward to meeting you!

Best regards,
HR Onboarding Team"""

    if not model:
        print("[AI Agent] No Gemini API key configured. Using local fallback response generation.")
        return generate_onboarding_response_fallback(employee, missing_fields, employee_question)

    kb_context = get_kb_context()
    
    prompt = f"""
    You are an AI HR onboarding assistant.
    
    Employee Name: {employee.name}
    
    {kb_context}
    
    Employee Question:
    {employee_question if employee_question else "None"}
    
    Missing Onboarding Fields:
    {missing_fields if missing_fields else "None"}
    
    Write a professional email response.
    
    Rules:
    1. Answer the employee's question accurately using ONLY the provided Predefined Company Knowledge Base. If the question is not answered in the Knowledge Base, reply politely that you will consult with the HR team and get back to them.
    2. If there are missing fields, politely ask the employee to reply with them in the same thread. Specifically, if Date of Birth is missing, ask for it in the format: DD/MM/YYYY.
    3. If all fields are complete (no missing fields), congratulate the employee and confirm that their onboarding is complete. Do NOT proactively provide information from the knowledge base (like dress code or office address) unless the employee specifically asked a question about it.
    4. Sign off professionally as the HR Onboarding Team.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"[AI Agent] Gemini reply generation failed: {e}. Falling back to template.")
        return generate_onboarding_response_fallback(employee, missing_fields, employee_question)

def generate_onboarding_response_fallback(employee, missing_fields, employee_question):
    body = f"Hi {employee.name},\n\n"
    
    # 1. Answer any question
    if employee_question:
        answer = search_kb_fallback(employee_question)
        if answer:
            body += f"{answer}\n\n"
        else:
            # Custom questions default reply
            body += "Regarding your question, I will verify the details with the HR team and get back to you shortly.\n\n"
            
    # 2. Handle missing details
    if missing_fields:
        body += "To complete your onboarding process, we still require the following information:\n"
        for field in missing_fields:
            if field == "Date of Birth":
                body += f"- {field} (e.g., DD/MM/YYYY)\n"
            else:
                body += f"- {field}\n"
        body += "\nPlease reply directly to this email with these details."
    else:
        body += "Your onboarding completion is done. We look forward to meeting you!"
        
    body += "\n\nBest regards,\nHR Onboarding Team"
    return body