"""Google Sheets append helper using a service account."""

import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build


def _get_credentials():
    """Load credentials from the JSON stored in the env var."""
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON")
    if not creds_json:
        raise RuntimeError("Missing GOOGLE_SHEETS_CREDENTIALS_JSON environment variable.")

    info = json.loads(creds_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    return service_account.Credentials.from_service_account_info(info, scopes=scopes)


def append_row(date: str, description: str, amount: float):
    """Append a single expense row to the configured sheet."""
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    sheet_range = os.environ.get("GOOGLE_SHEET_RANGE", "Sheet1!A:C")

    if not sheet_id:
        raise RuntimeError("Missing GOOGLE_SHEET_ID environment variable.")

    creds = _get_credentials()
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    sheets = service.spreadsheets()

    body = {
        "values": [[date, description, amount]],
    }

    result = (
        sheets.values()
        .append(
            spreadsheetId=sheet_id,
            range=sheet_range,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )

    return result
