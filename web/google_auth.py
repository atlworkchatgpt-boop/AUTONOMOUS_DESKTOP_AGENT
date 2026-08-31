import os

from authlib.integrations.starlette_client import OAuth


GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID"
)

GOOGLE_CLIENT_SECRET = os.getenv(
    "GOOGLE_CLIENT_SECRET"
)

GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://127.0.0.1:8000/auth/callback"
)


oauth = OAuth()


if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:

    oauth.register(
        name="google",

        client_id=GOOGLE_CLIENT_ID,

        client_secret=GOOGLE_CLIENT_SECRET,

        server_metadata_url=(
            "https://accounts.google.com/"
            ".well-known/openid-configuration"
        ),

        client_kwargs={
            "scope": (
                "openid "
                "email "
                "profile "
                "https://www.googleapis.com/auth/gmail.send"
            )
        },

    )


def google_configured():

    return bool(
        GOOGLE_CLIENT_ID
        and
        GOOGLE_CLIENT_SECRET
    )
