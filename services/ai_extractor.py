import re
from dateutil import parser

def clean_prefix(text):
    if not text:
        return text
    # Strip common filler prefix words like "my ", "a ", "an ", "the ", "in "
    clean = re.sub(r'^(?:my|a|an|the|in|at|from)\s+', '', text, flags=re.IGNORECASE)
    return clean.strip()

def extract_details(text):
    data = {
        "qualification": None,
        "location": None,
        "dob": None
    }
    
    # Split text into sentences/clauses
    # Only split at periods that are followed by spaces (sentence boundary) to preserve B.Tech, M.Tech, etc.
    clauses = re.split(r'\.\s+|\s*[\!\?\n\r]+\s*|\s+\band\b\s+', text)
    clauses = [c.strip() for c in clauses if c.strip()]
    
    # 1. Extract Qualification
    for clause in clauses:
        # Match "completed B.Tech", "did BE", "have graduation in MCA", "qualification is BCA"
        q_match = re.search(
            r"(?:completed|did|have|degree in|graduation in|studied|studied in|qualification is)\s+([a-zA-Z0-9\.\s\-\(\)\/]{2,30})",
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
        # Match "live in Pune", "located in Noida", "based in Bangalore", "location is Noida", "from Pune"
        l_match = re.search(
            r"(?:live in|located in|based in|from|at|location is|living in)\s+([a-zA-Z\s]{2,25})",
            clause,
            re.IGNORECASE
        )
        if l_match:
            data["location"] = clean_prefix(l_match.group(1))
            break

    # 3. Extract DOB
    for clause in clauses:
        # Match "DOB is 12 March 2003", "born on...", "date of birth is...", "dob: ..."
        d_match = re.search(
            r"(?:dob is|born on|date of birth is|birth date is|birthdate is|dob:?)\s+([a-zA-Z0-9\s\,\-\/]+)",
            clause,
            re.IGNORECASE
        )
        if d_match:
            dob_str = d_match.group(1).strip()
            try:
                parsed_date = parser.parse(dob_str, fuzzy=True)
                data["dob"] = parsed_date.date()
                break
            except:
                pass
                
        # Fallback: scan for any stand-alone date format (e.g. 12 March 2003, 12-03-2003)
        d_standalone = re.search(
            r"\b(\d{1,2}\s+[a-zA-Z]{3,9}\s+\d{4}|[a-zA-Z]{3,9}\s+\d{1,2}\,\s+\d{4}|\d{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{4}|\d{4}[\-\/\.]\d{1,2}[\-\/\.]\d{1,2})\b",
            clause
        )
        if d_standalone:
            try:
                parsed_date = parser.parse(d_standalone.group(1), fuzzy=True)
                data["dob"] = parsed_date.date()
                break
            except:
                pass

    return data