import base64
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def send_gmail(
    access_token,
    refresh_token,
    client_id,
    client_secret,
    to_email,
    subject,
    body
):

    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=[
            "https://www.googleapis.com/auth/gmail.send"
        ]
    )

    service = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    message = EmailMessage()

    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body)

    encoded = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    result = service.users().messages().send(
        userId="me",
        body={
            "raw": encoded
        }
    ).execute()

    return result
