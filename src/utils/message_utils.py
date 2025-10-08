def convert_from_whatsapp_number_format(phone_number):
    """
    Processes the raw phone number string to remove 'whatsapp:' prefix if present.
    """
    if phone_number:
        phone_number = phone_number.replace('whatsapp:', '', 1)
    return phone_number


def convert_to_whatsapp_number_format(phone_number):
    """
    Processes the raw phone number string to add 'whatsapp:'
    """
    to_whatsapp_number = 'whatsapp:' + phone_number
    return to_whatsapp_number


