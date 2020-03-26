from jira import JIRA
import re
import os

user_ids = os.environ['JIRA_USER_IDS'].split(',')

TEAM = [
  {
    "name": "marceloc",
    "id": user_ids[0]
  },
  {
    "name": "atharvar",
    "id": user_ids[1]
  },
  {
    "name": "haraprasadj",
    "id": user_ids[2]
  },
]


options = {
  'server': 'https://ctds-planx.atlassian.net'
}
jira = JIRA(options, basic_auth=('ctds.qa.automation@gmail.com', os.environ["JIRA_API_TOKEN"]))

PROJECT_NAME = "PXP"
RELEASE_TITLE = "CREATED BY AUTOMATION - PLEASE IGNORE - April 2020 03 Gen3 Core Release"
COMPONENT = 'Team Catch(Err)'
RELEASE_EPIC = jira.issue("PXP-5716")

print("start adding tasks to " + RELEASE_TITLE)

for member in TEAM:
    issue_dict = {
        'project': PROJECT_NAME,
        'summary': RELEASE_TITLE + " " + member['name'],
        'description': 'Task A, B and C',
        'issuetype': {'name': 'Task'},
        'components': [{'name': COMPONENT}],
        'assignee': {'accountId': member['id'] }
    }
    new_issue = jira.create_issue(fields=issue_dict)
    jira.add_issues_to_epic(RELEASE_EPIC.id, [new_issue.key])
    print(member['name'] + " is processed")
print ("done")
