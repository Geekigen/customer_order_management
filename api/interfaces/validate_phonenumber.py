def validate_phone_number(phone_number):
    """
    Validates a phone number in the format +COUNTRYCODE+DIGITS
    Example: +254719485369

    Args:
        phone_number (str): The phone number to validate

    Returns:
        bool: True if the phone number is valid, False otherwise
    """
    import re

    pattern = r'^\+[1-9]\d{0,2}\d{6,12}$'

    return bool(re.match(pattern, phone_number))
