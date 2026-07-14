# Predefined Knowledge Base for Onboarding Agent

KNOWLEDGE_BASE = {
    "documents": (
        "Mandatory documents required on your first day:\n"
        "1. Educational certificates (10th, 12th, Graduation, and Post-Graduation marksheets/degrees).\n"
        "2. Relieving letter & Experience letters from all previous employers.\n"
        "3. Copy of Aadhar Card, PAN Card, and Passport (if available).\n"
        "4. 4 Passport-size color photographs.\n"
        "5. Cancelled cheque or Bank passbook copy for salary account setup."
    ),
    "dress_code": (
        "Our office dress code is Smart Casual (collared shirts, polo shirts, trousers, chinos, smart jeans, and shoes).\n"
        "Casuals (t-shirts, sneakers) are allowed on Fridays. Ripped clothing and beachwear are prohibited."
    ),
    "timings": (
        "Our official working hours are 9:30 AM to 6:30 PM, Monday through Friday.\n"
        "We follow a hybrid model: 3 days working from the office (Tuesday, Wednesday, Thursday) and 2 days remote (Monday, Friday)."
    ),
    "formalities": (
        "Your first-day joining formalities will begin at 9:30 AM at the reception.\n"
        "This includes: filling out joining forms, document verification, biometric registration, IT asset setup (laptop/emails), "
        "and an induction session with your HR partner and team manager."
    ),
    "location": (
        "Our office address is:\n"
        "Kharadi, CargoFL in City Vista."
    )
}

def get_kb_context():
    context = "Predefined Company Knowledge Base:\n"
    for key, val in KNOWLEDGE_BASE.items():
        context += f"Topic: {key.upper()}\nInformation: {val}\n\n"
    return context

def search_kb_fallback(text):
    """
    Simple keyword-based fallback search to answer questions when Gemini is not available.
    """
    text = text.lower()
    answers = []
    
    if any(k in text for k in ["document", "doc", "certificate", "paperwork"]):
        answers.append("Regarding documents: " + KNOWLEDGE_BASE["documents"])
    if any(k in text for k in ["dress", "wear", "attire", "clothes"]):
        answers.append("Regarding dress code: " + KNOWLEDGE_BASE["dress_code"])
    if any(k in text for k in ["timing", "hour", "schedule", "work policy", "hybrid"]):
        answers.append("Regarding timings: " + KNOWLEDGE_BASE["timings"])
    if any(k in text for k in ["formality", "first day", "joining details", "orientation", "induction"]):
        answers.append("Regarding joining formalities: " + KNOWLEDGE_BASE["formalities"])
    if any(k in text for k in ["location", "address", "where", "office", "metro", "reach"]):
        answers.append("Regarding office location: " + KNOWLEDGE_BASE["location"])
        
    if answers:
        return "\n\n".join(answers)
    return None
