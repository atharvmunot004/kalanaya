from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Get project root directory (3 levels up from this file)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_CREDENTIALS_DIR = _PROJECT_ROOT / "credentials"
CREDENTIALS_FILE = _CREDENTIALS_DIR / "google_client_secret.json"
TOKEN_FILE = _CREDENTIALS_DIR / "token.pickle"


def get_calendar_service():
    creds = None

    # Load existing token if available
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Credentials file not found at {CREDENTIALS_FILE}. "
                    "Please ensure google_client_secret.json is in the credentials/ directory."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for next runs
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service
