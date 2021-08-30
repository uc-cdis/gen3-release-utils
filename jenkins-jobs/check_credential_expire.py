import jwt
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import sys
import os


def main():
    credential_filepath = sys.argv[1]
    slack_client = WebClient(token=sys.argv[2])
    CHANNEL_ID = sys.argv[3]

    if os.path.exists(credential_filepath):
        credential = open(credential_filepath)
        api_key = json.load(credential)["api_key"]
        expire_timestamp = jwt.decode(api_key, options={"verify_signature": False})[
            "exp"
        ]
        expire_datetime = datetime.fromtimestamp(expire_timestamp)
        print(f"### ## expire datetime: {expire_datetime}")
        now_datetime = datetime.now()
        print(f"### ## now datetime: {now_datetime}")
        expired = now_datetime > expire_datetime
        if expired:
            try:
                result = slack_client.chat_postMessage(
                    channel=CHANNEL_ID,
                    text="The credential file of qa-dcp expired:exclamation: Check it here: https://jenkins.planx-pla.net/credentials/store/system/domain/_/credential/qa-dcp-credentials-json/",
                    icon_emoji=":fire_engine:",
                    username="qa-bot",
                )
            except SlackApiError as e:
                print(f"Error posting message: {e}")
        else:
            print("credential is not expired")
    else:
        raise FileNotFoundError("Credentail file not found!")


if __name__ == "__main__":
    main()
