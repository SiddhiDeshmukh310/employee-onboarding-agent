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

def extract_employee_info(email_text):
    if not model:
        print("[AI Agent] No Gemini API key configured. Using local fallback extraction.")
        return extract_employee_info_fallback(email_text)

    prompt = f"""
    You are an HR onboarding AI.
    Extract the following information from the email text:
    - qualification
    - dob (Format strictly as YYYY-MM-DD. Extract date of birth if mentioned in any format like '12 March 2003' or '12-03-2003' or 'May 12 1996')
    - location
    - employee_question (Any question the employee is asking. If none, write null)

    Return ONLY a valid JSON object. Do not wrap in markdown or code blocks.
    
    Example:
    {{
        "qualification": "BE Computer Engineering",
        "dob": "2003-03-12",
        "location": "Pune",
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
    
    question_triggers = ["documents", "docs", "joining details", "dress", "timings", "hybrid", "working hours", "where", "location", "address", "metro"]
    for trigger in question_triggers:
        if trigger in email_lower:
            question = f"What are the details regarding {trigger}?"
            break
            
    # Format dob to string if it was parsed as date
    dob_str = None
    if details.get("dob"):
        try:
            dob_str = details["dob"].strftime("%Y-%m-%d")
        except:
            dob_str = str(details["dob"])

    return {
        "qualification": details.get("qualification"),
        "dob": dob_str,
        "location": details.get("location"),
        "employee_question": question
    }

def generate_onboarding_response(employee, missing_fields, employee_question):
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
    2. If there are missing fields, politely ask the employee to reply with them in the same thread.
    3. If all fields are complete (no missing fields), congratulate the employee and confirm that their onboarding is complete.
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
            body += f"- {field}\n"
        body += "\nPlease reply directly to this email with these details."
    else:
        body += "Thank you for providing all the required information! Your onboarding process is now complete. We look forward to welcoming you to the company!"
        
    body += "\n\nBest regards,\nHR Onboarding Team"
    return body