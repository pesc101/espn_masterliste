"""
Column-name configuration.

If your CSV/XLS export uses different headers, only change the values here –
no other file needs to be touched.
"""

# Logical key → actual CSV column name
COL: dict[str, str] = {
    # Orders export (English column names, comma-separated)
    "order_id": "Order number",
    "item": "Item",
    "price": "Price",
    "email": "Contact email",
    "date_created": "Date created",
    "billing_address": "Billing address",
    "billing_city": "Billing city",
    "billing_zip": "Billing zip/postal code",
    "billing_country": "Billing country",
    "billing_state": "Billing state",
    "billing_company": "Billing company name",
    # Contacts export (English column names, comma-separated)
    "contact_email": "Email 1",
    "title": "Titel",
    "first_name": "First Name",
    "last_name": "Last Name",
    "phone": "Phone 1",
    "birthdate": "Birthdate",
    "gender": "Gender",
    # Contacts – primary address (Address 1)
    "addr1_street": "Address 1 - Street",
    "addr1_city": "Address 1 - City",
    "addr1_state": "Address 1 - State/Region",
    "addr1_zip": "Address 1 - Zip",
    "addr1_country": "Address 1 - Country",
    # Contacts – secondary address (Address 2)
    "addr2_type": "Address 2 - Type",
    "addr2_street": "Address 2 - Street",
    "addr2_city": "Address 2 - City",
    "addr2_state": "Address 2 - State/Region",
    "addr2_zip": "Address 2 - Zip",
    "addr2_country": "Address 2 - Country",
    # Contacts – tertiary address (Address 3)
    "addr3_type": "Address 3 - Type",
    "addr3_street": "Address 3 - Street",
    "addr3_city": "Address 3 - City",
    "addr3_state": "Address 3 - State/Region",
    "addr3_zip": "Address 3 - Zip",
    "addr3_country": "Address 3 - Country",
    # Contacts – extra fields
    "company": "Company",
    "labels": "Labels",
    "created_at": "Created At (UTC+0)",
    "email_subscriber_status": "Email subscriber status",
    "sms_subscriber_status": "SMS subscriber status",
    "last_activity": "Last Activity",
    "last_activity_date": "Last Activity Date (UTC+0)",
    "source": "Source",
    "language": "Language",
}

# Preferred encodings per file type (tried in order on read failure)
ENCODING_FALLBACKS = ["utf-8", "latin-1"]
