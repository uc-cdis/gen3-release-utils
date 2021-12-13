# install google-api-python-client and google-auth-httplib2 google-auth-oauthlib
# enable "Google Calendar API"
# create a OAuth2.0 client ID and also create a API key
# add the Client ID credentials in the directory
# PlanX calendarID -> uchicago.edu_54c4a5nk50mm3gnt8n0m0s1j74@group.calendar.google.com

import datetime
import pickle
import os
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)

    event1 = {
        "summary": "Code Freeze",
        "description": "",
        "start": {"date": "2020-07-11", "timeZone": "America/Chicago"},
        "end": {"date": "2020-07-11", "timeZone": "America/Chicago"},
        "attendees": {
            {"email": " "},
        },
    }
    event = (
        service.events()
        .insert(
            calendarID="uchicago.edu_54c4a5nk50mm3gnt8n0m0s1j74@group.calendar.google.com",
            body=event1,
        )
        .execute()
    )
    print("CODE FREEZE event : %s" % (event.get("htmlLink")))

    event2 = {
        "summary": "Feature Freeze",
        "description": "",
        "start": {"date": "2020-07-11", "timeZone": "America/Chicago"},
        "end": {"date": "2020-07-11", "timeZone": "America/Chicago"},
        "attendees": {
            {"email": " "},
        },
    }
    event = (
        service.events()
        .insert(
            calendarID="uchicago.edu_54c4a5nk50mm3gnt8n0m0s1j74@group.calendar.google.com",
            body=event2,
        )
        .execute()
    )
    print("FEATURE FREEZE event : %s" % (event.get("htmlLink")))

    event3 = {
        "summary": "RELEASE PUBLICATION",
        "description": "",
        "start": {"date": "2020-07-11", "timeZone": "America/Chicago"},
        "end": {"date": "2020-07-11", "timeZone": "America/Chicago"},
        "attendees": {
            {"email": " "},
        },
    }
    event = (
        service.events()
        .insert(
            calendarID="uchicago.edu_54c4a5nk50mm3gnt8n0m0s1j74@group.calendar.google.com",
            body=event3,
        )
        .execute()
    )
    print("RELEASE PUBLICATION event : %s" % (event.get("htmlLink")))


if __name__ == "__main__":
    main()
