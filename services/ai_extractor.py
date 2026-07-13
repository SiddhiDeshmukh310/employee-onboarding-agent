import re
from dateutil import parser

def clean_prefix(text):
    if not text:
        return text
    # Strip common filler prefix words
    clean = re.sub(r'^(?:my|a|an|the|in|at|from|to|is|was|am|joining)\s+', '', text, flags=re.IGNORECASE)
    return clean.strip()

def extract_details(text):
    data = {
        "qualification": None,
        "location": None,
        "dob": None,
        "gender": None,
        "mobile_number": None,
        "alternate_mobile": None,
        "marital_status": None,
        "blood_group": None,
        "branch_depot": None
    }
    
    text_clean = text.replace('\r', '\n')
    clauses = re.split(r'[\n\t\.]+|\s+\band\b\s+', text_clean)
    clauses = [c.strip() for c in clauses if c.strip()]
    
    # 1. Extract Qualification
    for clause in clauses:
        q_match = re.search(
            r"(?:completed|did|have|degree in|graduation in|studied|studied in|qualification is|qualification\s*\:|qual\s*\:|qual\b|qualification\b|degree\s*\:|degree\b|education\s*\:|education\b)\s+([a-zA-Z0-9\.\s\-\(\)\/]{2,30})",
            clause,
            re.IGNORECASE
        )
        if q_match:
            data["qualification"] = clean_prefix(q_match.group(1))
            break
            
        q_direct = re.search(
            r"\b(b\.?tech|m\.?tech|b\.?e|m\.?ca|b\.?sc|b\.?ca|ph\.?d|m\.?ba|graduation|post\s*-?\s*graduation|bachelor|master|diploma)\b\s*([a-zA-Z0-9\s\-\(\)\/]*)",
            clause,
            re.IGNORECASE
        )
        if q_direct:
            data["qualification"] = clean_prefix(q_direct.group(0))
            break

    # 2. Extract Location
    for clause in clauses:
        l_match = re.search(
            r"(?:live in|located in|based in|from|at|location is|living in|residing in|staying in|location\s*\:|loc\s*\:|loc\b|location\b|city\s*\:|city\b|place\s*\:|place\b)\s+([a-zA-Z\s]{2,25})",
            clause,
            re.IGNORECASE
        )
        if l_match:
            data["location"] = clean_prefix(l_match.group(1))
            break

    # 3. Extract DOB
    for clause in clauses:
        d_match = re.search(
            r"(?:dob is|born on|date of birth is|birth date is|birthdate is|dob:?|date of birth:?|dob\s*\:|date of birth\s*\:|dob|date of birth|birthdate|birth date|bday|b-day|bdate|bday\s*\:|bdate\s*\:)\s+([a-zA-Z0-9\s\,\-\/]+)",
            clause,
            re.IGNORECASE
        )
        if d_match:
            dob_str = d_match.group(1).strip()
            try:
                parsed_date = parser.parse(dob_str, fuzzy=True)
                data["dob"] = parsed_date.strftime("%Y-%m-%d")
                break
            except:
                pass
                
        d_standalone = re.search(
            r"\b(\d{1,2}\s+[a-zA-Z]{3,9}\s+\d{4}|[a-zA-Z]{3,9}\s+\d{1,2}\,\s+\d{4}|\d{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{4}|\d{4}[\-\/\.]\d{1,2}[\-\/\.]\d{1,2})\b",
            clause
        )
        if d_standalone:
            try:
                parsed_date = parser.parse(d_standalone.group(1), fuzzy=True)
                data["dob"] = parsed_date.strftime("%Y-%m-%d")
                break
            except:
                pass

    # 4. Extract Gender (Scan closed set)
    gender_lower = text.lower()
    if "female" in gender_lower:
        data["gender"] = "Female"
    elif "male" in gender_lower:
        data["gender"] = "Male"
    elif "other" in gender_lower:
        data["gender"] = "Other"

    # 5 & 6. Extract Mobile Numbers (Smart phone-like pattern scanning)
    phone_matches = re.findall(r"\b(\+?\d[\d\s\-]{8,14}\d)\b", text)
    cleaned_phones = []
    for p in phone_matches:
        c = re.sub(r'[\s\-]', '', p)
        if len(c) >= 10:  # Validate length
            cleaned_phones.append(p.strip())
            
    if cleaned_phones:
        if len(cleaned_phones) >= 2:
            data["mobile_number"] = cleaned_phones[0]
            data["alternate_mobile"] = cleaned_phones[1]
        else:
            data["mobile_number"] = cleaned_phones[0]

    # 7. Extract Marital Status (Scan closed set)
    status_lower = text.lower()
    if "single" in status_lower:
        data["marital_status"] = "Single"
    elif "married" in status_lower:
        data["marital_status"] = "Married"
    elif "divorced" in status_lower:
        data["marital_status"] = "Divorced"
    elif "widow" in status_lower:
        data["marital_status"] = "Widow"

    # 8. Extract Blood Group (Scan closed set patterns)
    bg_match = re.search(r"\b(A\+|A\-|B\+|B\-|AB\+|AB\-|O\+|O\-)\b", text, re.IGNORECASE)
    if bg_match:
        data["blood_group"] = bg_match.group(1).upper()

    # 9. Extract Branch / Depot (Supports both label-first and value-first formats)
    for clause in clauses:
        # A. Label-first: "branch: Bhekarainagar"
        br_match1 = re.search(
            r"(?:branch depot|branch / depot|branch|depot)\s+(?:is|at|to|:\s*)\s*([a-zA-Z0-9\s]{2,25})",
            clause,
            re.IGNORECASE
        )
        if br_match1:
            val = br_match1.group(1).strip()
            val = re.sub(r'\b(?:office|location|depot|branch)\b.*', '', val, flags=re.IGNORECASE).strip()
            data["branch_depot"] = clean_prefix(val)
            break
            
        # B. Value-first: "Bhekarainagar branch"
        br_match2 = re.search(
            r"\b([a-zA-Z0-9\s]{2,25})\s+(?:branch|depot)\b",
            clause,
            re.IGNORECASE
        )
        if br_match2:
            val = br_match2.group(1).strip()
            val = re.sub(r'.*\b(?:joining|at|the)\s+', '', val, flags=re.IGNORECASE).strip()
            data["branch_depot"] = clean_prefix(val)
            break

    return data