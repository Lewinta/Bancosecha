import frappe
import re

def validate(doc, method):
    validate_phone_number(doc)

def validate_phone_number(doc):
    if doc.custom_phone_number:
        # Remove spaces, dashes, parentheses, and plus signs
        cleaned_number = re.sub(r'[\s\-()+]', '', doc.custom_phone_number)
        if cleaned_number != doc.custom_phone_number:
            doc.custom_phone_number = cleaned_number