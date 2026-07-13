import re
from dateutil import parser


def extract_details(text):
    data = {
        "qualification": None,
        "location": None,
        "dob": None
    }

    q = re.search(
        r"qualification is (.+)",
        text,
        re.IGNORECASE
    )

    if q:
        data["qualification"] = q.group(1).strip().rstrip(".")

    l = re.search(
        r"live in (.+)",
        text,
        re.IGNORECASE
    )

    if l:
        data["location"] = l.group(1).strip().rstrip(".")

    d = re.search(
        r"date of birth is (.+)",
        text,
        re.IGNORECASE
    )

    if d:
        try:
            dob = parser.parse(d.group(1))
            data["dob"] = dob.date()
        except:
            pass

    return data