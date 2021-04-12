from jira import JIRA
import re
import os
import sys
import datetime

release = os.environ["RELEASE"]

options = {"server": "https://ctds-planx.atlassian.net"}
jira = JIRA(
    options, basic_auth=(os.environ["JIRA_SVC_ACCOUNT"], os.environ["JIRA_API_TOKEN"])
)

tasks = [
    {
        "title": "0. Create RELEASE {} in JIRA".format(release),
        "description": "Kick off this job: https://jenkins.planx-pla.net/job/create-gen3-release-in-jira/",
    },
    {
        "title": "1. Cut the integration branch integration{}".format(
            release.replace(".", "")
        ),
        "description": "Kick off this job: https://jenkins.planx-pla.net/job/create-gen3-release-candidate-branch/",
    },
    {
        "title": "2. Create gitops-qa PRs to deploy the integration branch to QA environments",
        "description": "Run the folling command to apply the integration branch images against the target QA environment: python gen3release/env_cli.py apply -v integration2020<nn> -e ~/workspace/gitops-qa/qa-<environment>.planx-pla.net",
    },
    {
        "title": "3. Generate release notes and publish release manifest into `cdis-manifest/<year>/<month>` folder",
        "description": "Generate the release notes with this Jenkins job: https://jenkins.planx-pla.net/job/gen3-qa-monthly-release-notes-generator. The cdis-manifest PR is tailored manually and it should include release notes and known bugs files (the PR must be labeled with `doc-only`).",
    },
    {
        "title": "SHARED: 4. Release testing round: automated tests and manual tests against qa envs",
        "description": 'Full list of tests tracked in the "Test Plan - Gen3 Releases" spreadsheet',
    },
    {
        "title": "5. Run load tests on qa-dcp and store json files with results for benchmarking purposes",
        "description": "Run the following load scenarios: fence-presigned-url, sheepdog-import-clinical-metada, metadata-service-create-and-query and metadata-service-filter-large-database. Just kick off this job https://jenkins.planx-pla.net/job/gen3-run-load-tests/ and store the result.json files accordingly.",
    },
    {
        "title": "6. Merge the integration branch into stable and tag the release",
        "description": "Kick off this job: https://jenkins.planx-pla.net/job/merge-integration-branch-into-stable-and-tag/. Once the tag-based images are built in Quay, sanity check the images by creating a `gitops-qa` PR to deploy them against one of the QA environments.",
    },
    {
        "title": "7. Pushing monthly release quay images to AWS ECR (as a backup)",
        "description": "Kick off this job: https://jenkins.planx-pla.net/job/push-gen3-monthly-release-images-to-aws-ecr. Also double-check if the repos_list.txt is up-to-date.",
    },
    {
        "title": "SHARED: 8. Follow up with PMs to merge the PRs of respective commons",
        "description": "The `automerge` label is applied automatically to all PRs, once the PM approves it, the changes will be automatically merged and deployed to the environment. The QA engineers should monitor the PRs in case of any CI check failures.",
    },
    {
        "title": "9. Mark the release as released",
        "description": "Kick off this job: https://jenkins.planx-pla.net/job/mark-gen3-monthly-release-as-released.",
    },
]

user_ids = os.environ["JIRA_USER_IDS"].split(",")

team_members = [
    # {"name": "haraprasadj", "id": user_ids[3]},
    {"name": "jingh8", "id": user_ids[2]},
    {"name": "atharvar", "id": user_ids[1]},
    {"name": "marceloc", "id": user_ids[0]},
]

# set initial team member index based on the number of the month
# every month a diff team member will pick a diff task
year_and_month = re.search(r"([0-9]{4})\.([0-9]{2})", release)
team_member_index = int(year_and_month.group(2)) % len(team_members)

# get year
year = year_and_month.group(1)
# get month string
month = datetime.date(1900, int(year_and_month.group(2)), 1).strftime("%B")

# Do not create duplicate Epic + Tasks
query = jira.search_issues(
    jql_str='issuetype = Epic AND project = {} AND text ~ "{} {} Gen3 Core Release"'.format(
        os.environ["JIRA_PROJECT_NAME"], month, year
    )
)

if len(query) > 0:
    print(
        "Epic for {} release [{}] already exists. Abort automatic creation of tickets...".format(
            release, query[0]
        )
    )
    sys.exit(1)

PROJECT_NAME = os.environ["JIRA_PROJECT_NAME"]
RELEASE_TITLE = "{} {} Gen3 Core Release".format(month, year)
COMPONENTS = [
    {"name": "Team Catch(Err)"},
]

epic_dict = {
    "project": PROJECT_NAME,
    "customfield_10011": RELEASE_TITLE,
    "summary": RELEASE_TITLE,
    "description": "This epic comprises all the tasks releated to {}".format(
        RELEASE_TITLE
    ),
    "issuetype": {"name": "Epic"},
    "components": COMPONENTS,
    "assignee": {"accountId": team_members[team_member_index]["id"]},
}

new_epic = jira.create_issue(fields=epic_dict)
RELEASE_EPIC = new_epic.key

print("start adding tasks to " + RELEASE_TITLE)


def create_ticket(issue_dict, team_member_index):
    new_issue = jira.create_issue(fields=issue_dict)
    jira.add_issues_to_epic(RELEASE_EPIC, [new_issue.key])
    print(
        team_members[team_member_index]["name"]
        + " has been assigned to "
        + task["title"]
    )
    return new_issue.key


for task in tasks:
    summary = task["title"]
    issue_dict = {
        "project": PROJECT_NAME,
        "summary": summary,
        "description": task["description"],
        "issuetype": {"name": "Story"},
        "components": COMPONENTS,
        "assignee": {"accountId": team_members[team_member_index]["id"]},
    }
    # Shared tasks required one ticket per team member
    if task["title"].split(":")[0] == "SHARED":
        summary = issue_dict["summary"]
        for i in range(0, len(team_members)):
            issue_dict["summary"] = summary + " - " + team_members[i]["name"]
            issue_dict["assignee"] = {"accountId": team_members[i]["id"]}
            jira_id = create_ticket(issue_dict, i)
    else:
        issue_dict["assignee"] = {"accountId": team_members[team_member_index]["id"]}
        team_member_index = (team_member_index + 1) % len(team_members)
        jira_id = create_ticket(issue_dict, team_member_index)

print("done")
