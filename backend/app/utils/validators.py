import re
from typing import Optional, Tuple

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@gmail\.com$")
PHONE_REGEX = re.compile(r"^\+?[0-9]{10,15}$")

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip()))

def is_valid_mobile(mobile: str) -> bool:
    cleaned = re.sub(r"[\s\-()]", "", mobile.strip())
    return bool(PHONE_REGEX.match(cleaned))

def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        return False, "Password must contain at least one letter and one number."
    return True, None
