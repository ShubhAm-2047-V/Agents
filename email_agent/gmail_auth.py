"""
gmail_auth.py
Handles Gmail OAuth login. First run opens a browser for you to approve
access - after that, the token is cached locally so it just works silently.

Uses google-auth-oauthlib + google-api-python-client, both free/official
Google libraries. No Gmail-side cost - the Gmail API itself has a very
generous free quota (1 billion quota units/day, far beyond personal use).
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import config


def get_gmail_service():
    """
    Returns an authenticated Gmail API service object.
    Handles first-time OAuth login and token refresh automatically.
    """
    creds = None

    if os.path.exists(config.TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(config.TOKEN_PATH, config.SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(config.CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Missing {config.CREDENTIALS_PATH}. Download your OAuth "
                    f"credentials.json from Google Cloud Console and place it "
                    f"in this folder - see README.md for steps."
                )
            flow = InstalledAppFlow.from_client_secrets_file(config.CREDENTIALS_PATH, config.SCOPES)
            creds = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(config.TOKEN_PATH), exist_ok=True)
        with open(config.TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)
