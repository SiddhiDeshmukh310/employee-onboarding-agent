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
    "location": (
        "CargoFL Pune Kharadi"
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
    if any(k in text for k in ["location", "address", "where", "office", "reach", "pune", "kharadi"]):
        answers.append("Regarding office location: " + KNOWLEDGE_BASE["location"])
        
    if answers:
        return "\n\n".join(answers)
    return None
