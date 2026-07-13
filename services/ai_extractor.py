import re
from dateutil import parser

def clean_prefix(text):
    if not text:
        return text
    # Strip common filler prefix words like "my ", "a ", "an ", "the ", "in ", "at ", "from "
    clean = re.sub(r'^(?:my|a|an|the|in|at|from)\s+', '', text, flags=re.IGNORECASE)
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
    
    # Split text into sentences/clauses
    clauses = re.split(r'[\n\r\t]+|\s+\band\b\s+|\.\s+', text)
    clauses = [c.strip() for c in clauses if c.strip()]
    
    # 1. Extract Qualification
    for clause in clauses:
        # Match "completed B.Tech", "Qualification BE", "qualification: BE", etc.
        q_match = re.search(
            r"(?:completed|did|have|degree in|graduation in|studied|studied in|qualification is|qualification\s*\:|qual\s*\:|qual\b|qualification\b|degree\s*\:|degree\b|education\s*\:|education\b)\s+([a-zA-Z0-9\.\s\-\(\)\/]{2,30})",
            clause,
            re.IGNORECASE
        )
        if q_match:
            data["qualification"] = clean_prefix(q_match.group(1))
            break
            
        # Match direct standalone degree mention
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
        # Match "live in Pune", "Location Pune", "location: Pune", etc.
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
        # Match "DOB 12 March 2003", "Date of birth 3/10/2004", "dob: 29/9/2003", etc.
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
                
        # Fallback: scan for any standalone date format (e.g. 29/9/2003)
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

    # 4. Extract Gender
    for clause in clauses:
        g_match = re.search(
            r"(?:gender is|gender\s*\:|gender)\s+(male|female|other|m|f)\b",
            clause,
            re.IGNORECASE
        )
        if g_match:
            g_val = g_match.group(1).strip().capitalize()
            if g_val == "M":
                g_val = "Male"
            elif g_val == "F":
                g_val = "Female"
            data["gender"] = g_val
            break

    # 5. Extract Mobile Number
    for clause in clauses:
        if "alternate" in clause.lower() or "alt" in clause.lower():
            continue
        mob_match = re.search(
            r"(?:mobile number is|contact number is|phone number is|mobile number\s*\:|mobile\s*\:|contact\s*\:|phone\s*\:|mobile|contact|phone)\s+(\+?\d[\d\-\s]{8,15}\d)",
            clause,
            re.IGNORECASE
        )
        if mob_match:
            data["mobile_number"] = mob_match.group(1).strip()
            break

    # 6. Extract Alternate Mobile Number
    for clause in clauses:
        alt_match = re.search(
            r"(?:alternate mobile number is|alternate mobile is|alt mobile is|alt contact is|alternate mobile\s*\:|alt mobile\s*\:|alternate contact\s*\:|alternate phone\s*\:|alt\s+contact\s*\:|alt\s+mobile\s*\:)\s+(\+?\d[\d\-\s]{8,15}\d)",
            clause,
            re.IGNORECASE
        )
        if alt_match:
            data["alternate_mobile"] = alt_match.group(1).strip()
            break

    # 7. Extract Marital Status
    for clause in clauses:
        m_match = re.search(
            r"(?:marital status is|marital status\s*\:|marital status|marital\s+status|marital|status)\s+(single|married|divorced|widow)\b",
            clause,
            re.IGNORECASE
        )
        if m_match:
            data["marital_status"] = m_match.group(1).strip().capitalize()
            break

    # 8. Extract Blood Group
    for clause in clauses:
        b_match = re.search(
            r"(?:blood group is|blood group\s*\:|blood\s*\:|blood group|blood)\s+(A\+|A\-|B\+|B\-|AB\+|AB\-|O\+|O\-)",
            clause,
            re.IGNORECASE
        )
        if b_match:
            data["blood_group"] = b_match.group(1).strip().upper()
            break

    # 9. Extract Branch / Depot
    for clause in clauses:
        br_match = re.search(
            r"(?:branch depot is|branch / depot is|branch is|depot is|branch\s*\:|depot\s*\:|branch / depot\s*\:|branch depot\s*\:|branch depot|branch|depot)\s+([a-zA-Z0-9\s]{2,30})",
            clause,
            re.IGNORECASE
        )
        if br_match:
            data["branch_depot"] = clean_prefix(br_match.group(1))
            break

    return data