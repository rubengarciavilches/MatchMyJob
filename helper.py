import datetime

import PyPDF2


def fix_dict_str_or_none(d):
    if not isinstance(d, dict):
        raise ValueError("Input must be a dictionary.")

    # Create a list of items to modify the dictionary in-place
    items_to_modify = list(d.items())

    for key, value in items_to_modify:
        # Ensure the key is a string or NoneType, otherwise set it to None
        new_key = key if isinstance(key, (str, type(None))) else None

        # Ensure the value is a string or NoneType, otherwise set it to None
        new_value = value if isinstance(value, (str, type(None))) else None

        # Remove the original entry
        del d[key]

        # Add the fixed entry back to the dictionary
        d[new_key] = new_value


def now_formatted_datetime() -> str:
    now = datetime.datetime.utcnow()
    return now.isoformat()


def now_formatted_date() -> str:
    now = datetime.datetime.utcnow()
    return now.strftime("%Y-%m-%d")


def pdf_to_text(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
    return text
