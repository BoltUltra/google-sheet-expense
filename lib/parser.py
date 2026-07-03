"""Parse a free-text expense message into (date, description, amount)."""

import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser


def _extract_amount(text: str):
    """Return the first number found and its position, or (None, -1)."""
    # Match integers or decimals, possibly with commas as thousand separators
    pattern = re.compile(r"[\d,]+(?:\.\d{1,2})?")
    for match in pattern.finditer(text):
        raw = match.group().replace(",", "")
        try:
            return float(raw), match.start(), match.end()
        except ValueError:
            continue
    return None, -1, -1


def _strip_currency_symbols(text: str) -> str:
    return re.sub(r"[₦$€£¥]", "", text)


def _clean_description(description: str) -> str:
    """Remove connector words and currency symbols, normalize spacing."""
    description = _strip_currency_symbols(description)
    description = re.sub(r"\bon\b|\bfor\b", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\s+", " ", description).strip()
    return description


def _parse_date(text: str, today: datetime = None):
    """Try to find a date in the text. Return (date_obj, cleaned_text)."""
    if today is None:
        today = datetime.now()

    lowered = text.lower()

    # Relative days
    if "today" in lowered:
        return today.date(), re.sub(r"\btoday\b", "", text, flags=re.IGNORECASE)
    if "yesterday" in lowered:
        return (today - timedelta(days=1)).date(), re.sub(
            r"\byesterday\b", "", text, flags=re.IGNORECASE
        )

    # Try common explicit patterns
    date_patterns = [
        r"\b(\d{4}-\d{1,2}-\d{1,2})\b",           # 2026-07-05
        r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b",         # 07/05/2026
        r"\b(\d{1,2}\s+[a-zA-Z]{3,9}\s+\d{2,4})\b",  # 5 July 2026
        r"\b([a-zA-Z]{3,9}\s+\d{1,2}(?:\s*,?\s+\d{2,4})?)\b",  # July 5, 2026 or July 5
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(1)
            try:
                parsed = date_parser.parse(date_str, default=today)
                cleaned = text[: match.start()] + text[match.end() :]
                return parsed.date(), cleaned
            except (ValueError, OverflowError):
                continue

    return today.date(), text


def parse_expense(text: str):
    """
    Parse a message like 'Lunch 5000', 'Bought data 2000 yesterday',
    or 'Transport 1500 on July 1'.

    Returns a dict:
        {
            "date": "2026-07-03",
            "description": "Lunch",
            "amount": 5000.0,
            "currency": "₦",
        }

    Raises ValueError if amount cannot be found.
    """
    if not text or not text.strip():
        raise ValueError("Empty message.")

    # Normalize whitespace
    text = " ".join(text.split())

    # Detect and strip currency symbol for description purposes
    currency = "₦"
    if "₦" in text:
        currency = "₦"
    elif re.search(r"\$", text):
        currency = "$"
    elif re.search(r"€", text):
        currency = "€"
    elif re.search(r"£", text):
        currency = "£"

    amount, start, end = _extract_amount(text)
    if amount is None:
        raise ValueError("I couldn't find an amount in your message.")

    # Build description from text before and after the amount, dropping connector words
    before = text[:start].strip()
    after = text[end:].strip()

    # Try to parse date from the full text
    date_value, dateless_text = _parse_date(text)

    # Remove the amount and date from description
    description = dateless_text
    description = description.replace(text[start:end], " ")
    description = _clean_description(description)

    # Capitalize nicely
    description = description.capitalize()

    return {
        "date": date_value.isoformat(),
        "description": description,
        "amount": amount,
        "currency": currency,
    }
