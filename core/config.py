"""
Static configuration: column-name maps and output schemas.
"""

from __future__ import annotations

# ── Source-column name map ─────────────────────────────────────────────────────
COL: dict[str, str] = {
    # Orders export
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
    # Contacts export
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
    # Contacts – extra fields
    "company": "Company",
    "labels": "Labels",
    "language": "Language",
}

# ── Output column schemas ─────────────────────────────────────────────────────
# Matches the reference file: no "Membership Number #", includes "IPNA amount"
COLS_IPNA: list[str] = [
    "Titel",
    "First Name",
    "Last Name",
    "Email",
    "Phone",
    "Birthdate",
    "Address",
    "City",
    "Zipcode",
    "Country",
    "State",
    "Company",
    "Member since",
    "ESPN&IPNA amount",
    "IPNA amount",
    "Membership",
    "Gender",
    "Note",
]

# Matches the reference file: includes "Membership Number #", no "IPNA amount"
COLS_NEUE: list[str] = [
    "Membership Number #",
    "Titel",
    "First Name",
    "Last Name",
    "Email",
    "Phone",
    "Birthdate",
    "Address",
    "City",
    "Zipcode",
    "Country",
    "State",
    "Company",
    "Member since",
    "ESPN&IPNA amount",
    "Membership",
    "Gender",
    "Note",
]

# Vollständig uses the same schema as Neue Mitglieder
COLS_VOLL: list[str] = COLS_NEUE

# ── Encoding cascade used when auto-detecting CSV encoding ────────────────────
ENCODING_FALLBACKS: list[str] = [
    "utf-8",
    "windows-1252",
    "windows-1250",
    "latin-1",
    "ascii",
]
