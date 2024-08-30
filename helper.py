import datetime
from typing import List
import PyPDF2
from my_constants import DEFAULT_DELIMITER


def fix_dict_str_or_none(d):
    """
    Receives a dictionary and guarantees that every single item is valued either string or None.
    """
    if not isinstance(d, dict):
        raise ValueError("Input must be a dictionary.")
    items_to_modify = list(d.items())
    for key, value in items_to_modify:
        new_key = key if isinstance(key, (str, type(None))) else None
        new_value = value if isinstance(value, (str, type(None))) else None
        del d[key]
        d[new_key] = new_value


def parse_delimited_string(
    input_string: str, delimiter: str = DEFAULT_DELIMITER
) -> List[str]:
    return [item.strip() for item in input_string.split(delimiter)]


def list_to_delimited_string(
    input_list: List[str], delimiter: str = DEFAULT_DELIMITER
) -> str:
    return delimiter.join(input_list)


def now_formatted_datetime() -> str:
    now = datetime.datetime.utcnow()
    return now.isoformat()


def now_formatted_date() -> str:
    now = datetime.datetime.utcnow()
    return now.strftime("%Y-%m-%d")


def pdf_to_text(file_path):
    text = ""
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
    return text
