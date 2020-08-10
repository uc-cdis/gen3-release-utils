from jira import JIRA
import re
import os
import sys
import datetime

options = {"server": "https://ctds-planx.atlassian.net", "rest_api_version": "3"}
jira = JIRA(
    options, basic_auth=(os.environ["JIRA_SVC_ACCOUNT"], os.environ["JIRA_API_TOKEN"])
)

monthinteger = int(os.environ["RELEASE_VERSION"].split(".")[1])
month = datetime.date(1900, monthinteger, 1).strftime("%B")

result = jira.create_version(
    "{}".format(os.environ["RELEASE_VERSION"]),
    "PXP",
    description="Gen3 Release - {}".format(month),
    releaseDate=None,
    startDate=None,
    archived=False,
    released=False,
)

print("result: {}".format(result))
