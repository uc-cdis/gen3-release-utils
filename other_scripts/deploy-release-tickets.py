"""
Create tickets to deploy a version to a list of projects.
Usage:
JIRA_USERNAME=me@uchicago.edu JIRA_API_TOKEN=alo python deploy-release-tickets.py 2022.02

ENVS_DIST = { <project>: [<env>, <env>] }
=> To configure one story per project and one subtask per env.

To create a JIRA token:
https://id.atlassian.com/manage-profile/security/api-tokens

Custom field "Work to be Completed by:"
- id: "customfield_10067"
- allowed values:
  - value: "Product Team", id: "10054"
  - value: "Project Team", id: "10055"
"""


import json
import os
import requests
import sys


# parameters
ROOT_URL = os.environ["ROOT_URL"]
PROJECT_KEY = os.environ["PROJECT_KEY"]
COMPONENTS = os.environ["COMPONENTS"].split(",")
LABELS = os.environ["LABELS"].split(",")
ENVS = os.environ["ENVS"].split(",")

JIRA_USERNAME = os.environ["JIRA_USERNAME"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]
auth = (JIRA_USERNAME, JIRA_API_TOKEN)

ENVS_DICT = {
    "JCOIN": ["QA", "Prod"],
    "KidsFirst": ["QA", "external QA", "external Staging", "Prod"],
    "NCT": ["QA", "Prod"],
    "VA": ["va-testing", "Prod"],
    "MIDRC": ["Staging", "validate", "Prod"],
    "BDcat": ["Prod", "Preprod", "staging"],
    "Anvil": ["Prod", "staging", "internalstaging"],
    "HEAL": ["QA", "Pre-prod", "Prod", "externaldata"],
    "DCF": ["Staging", "Prod"],
    "COVID19": ["QA", "Prod"]
}


def create_deployment_tickets(project, envs, version):
    print(f"Creating ticket to deploy {version} to {project}")

    # create story for the project
    description = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"Deploy version {version} to {project}. If a monthly release newer than {version} is now available, check with the team to decide which version to deploy.",
                    }
                ],
            }
        ],
    }
    issue_data = {
        "fields": {
            "summary": f"{project}: deploy version {version}",
            "description": description,
            "project": {"key": PROJECT_KEY},
            "issuetype": {"name": "Story"},
            "customfield_10067": {"value": "Project Team"},
            "components": [{"name": c} for c in COMPONENTS],
            "labels": LABELS,
        }
    }
    res = requests.post(
        f"{ROOT_URL}/issue",
        json=issue_data,
        auth=auth,
        headers={"Content-type": "application/json"},
    )
    if res.status_code != 201:
        print(res.status_code, res.text)
        res.raise_for_status()
    issue_key = json.loads(res.text)["key"]
    print(f"  {issue_key}: {issue_data['fields']['summary']}")

    # create subtask for each env
    for env in envs:
        subtask_data = {
            "fields": {
                "summary": f"{version} to {project} {env}",
                "description": description,
                "project": {"key": PROJECT_KEY},
                "parent": {"key": issue_key},
                "issuetype": {"name": "Sub-task"},
                "customfield_10067": {"value": "Project Team"},
                "components": [{"name": c} for c in COMPONENTS],
            }
        }
        res = requests.post(
            f"{ROOT_URL}/issue",
            json=subtask_data,
            auth=auth,
            headers={"Content-type": "application/json"},
        )
        if res.status_code != 201:
            print(res.status_code, res.text)
            res.raise_for_status()
        subtask_key = json.loads(res.text)["key"]
        print(f"    {subtask_key}: {subtask_data['fields']['summary']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise Exception("Must specify a version to deploy")
    version = sys.argv[1]

    # uncomment below to look at / validate the project
    # res = requests.get(f"{ROOT_URL}/project/{PROJECT_KEY}", auth=auth)
    # if res.status_code != 200:
    #     print(res.status_code, res.text)
    #     res.raise_for_status()
    # jira_project = json.loads(res.text)
    # issueTypes = {it["name"]: it["id"] for it in jira_project["issueTypes"]}
    # assert "Story" in issueTypes
    # assert "Sub-task" in issueTypes
    # components = {it["name"]: it["id"] for it in jira_project["components"]}
    # for c in COMPONENTS:
    #     assert c in components

    for project in ENVS:
        envs = ENVS_DICT[project]
        create_deployment_tickets(project, envs, version)
