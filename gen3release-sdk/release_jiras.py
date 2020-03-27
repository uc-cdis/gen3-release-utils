from jira import JIRA
import re
import os
import sys
import datetime

release = os.environ['RELEASE']

options = {
  'server': 'https://ctds-planx.atlassian.net'
}
jira = JIRA(options, basic_auth=(os.environ["JIRA_SVC_ACCOUNT"], os.environ["JIRA_API_TOKEN"]))

tasks = [
  {
    'title': 'cut the integration branch integration{}'.format(release.replace('.','')),
    'description': 'At the end of the 2nd week of every other sprint we have to cut the integration branch. How to: ./make_branch.sh "master" "integration{}"'.format(release.replace('.',''))
  },
  {
    'title': 'create gitops-qa PRs to deploy the integration branch to QA environments',
    'description': 'Once the first manifest is ready, it can be replicated with: replicate_manifest_config.sh <remote_branch_in_gitops-qa>/qa-brain/manifest.json gitops-qa/qa-dcp.planx-pla.net/manifest.json. \n The QA team will collaborate to troubleshoot / debug whatever is necessary to make the PR checks pass (this should be done early in the 1st week of testing)'
  },
  {
    'title': 'SHARED: 2w release testing round: automated tests, manual tests and load tests against qa envs',
    'description': 'Full list of tests tracked in the "Test Plan - Gen3 Releases" spreadsheet'
  },
  {
    'title': 'merge the integration branch into stable and tag the release',
    'description': 'At the end of the 2nd week, we need to merge the integration branch into stable and tag the release (and make sure all Docker images are successfully built).'
  },
  {
    'title': 'publish release manifest cdis-manifest/<year>/<month> folder with release notes and knownbugs files',
    'description': 'Check instructions on the release mgmt guide'
  },
  {
    'title': 'SHARED: Prepare PRs in cdis-manifest to deploy the {} release to PROD environments'.format(release),
    'description': 'You can utilize the replicate_manifest_config.sh script to replicate changes between manifests'
  },
]

user_ids = os.environ['JIRA_USER_IDS'].split(',')

team_members = [
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

# set initial team member index based on the number of the month
# every month a diff team member will pick a diff task
year_and_month = re.search(r'([0-9]{4})\.([0-9]{2})', release)
team_member_index = int(year_and_month.group(2)) % len(team_members)

# get year
year = year_and_month.group(1)
# get month string
month = datetime.date(1900, int(year_and_month.group(2)), 1).strftime('%B')

# Do not create duplicate Epic + Tasks
query = jira.search_issues(
  jql_str='issuetype = Epic AND project = {} AND text ~ "{} {} Gen3 Core Release"'.format(os.environ['JIRA_PROJECT_NAME'], month, year)
)

if len(query) > 0:
  print('Epic for {} release [{}] already exists. Abort automatic creation of tickets...'.format(release, query[0]))
  sys.exit(1)

PROJECT_NAME = os.environ['JIRA_PROJECT_NAME']
RELEASE_TITLE = 'CREATED BY AUTOMATION - PLEASE IGNORE - {} {} Gen3 Core Release'.format(month, year)
COMPONENT = 'Team Catch(Err)'

epic_dict = {
  'project': PROJECT_NAME,
  'customfield_10011': RELEASE_TITLE,
  'summary': RELEASE_TITLE,
  'description': 'This epic comprises all the tasks releated to %s'.format(RELEASE_TITLE),
  'issuetype': {'name': 'Epic'},
  'components': [{'name': COMPONENT}],
  'assignee': {'accountId': team_members[team_member_index]['id'] }
}

new_epic = jira.create_issue(fields=epic_dict)
RELEASE_EPIC = new_epic.key

print("start adding tasks to " + RELEASE_TITLE)

def create_ticket(issue_dict, team_member_index):
    new_issue = jira.create_issue(fields=issue_dict)
    jira.add_issues_to_epic(RELEASE_EPIC, [new_issue.key])
    print(team_members[team_member_index]['name'] + " has been assigned to " + task['title'])
    return (team_member_index + 1) % len(team_members)

for task in tasks:
    print('team_member_index: ' + str(team_member_index))
    summary = task['title']
    issue_dict = {
        'project': PROJECT_NAME,
        'summary': summary,
        'description': task['description'],
        'issuetype': {'name': 'Task'},
        'components': [{'name': COMPONENT}],
        'assignee': {'accountId': team_members[team_member_index]['id'] }
    }
    # Shared tasks required one ticket per team member
    if task['title'].split(':')[0] == 'SHARED':
      for i in range(0, len(team_members)):
        print('inner loop team_member_index: ' + str(team_member_index))
        issue_dict['summary'] = issue_dict['summary'] + team_members[team_member_index]['name']
        team_member_index = create_ticket(issue_dict, team_member_index)
    else:
      team_member_index = create_ticket(issue_dict, team_member_index)
print ("done")
