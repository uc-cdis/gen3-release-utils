import os
import logging

from github import Github
from github.GithubException import UnknownObjectException
import pygit2
from pygit2 import RemoteCallbacks

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger(__name__)


class Git:
    def __init__(
        self, repo=None, username="PlanXCyborg", token="MEH-123", org="uc-cdis"
    ):
        """
     Creates a Github utils object to perform various operations against the uc-cdis repos and its branches, pull requests, etc.
    """
        self.org = org
        self.username = username
        self.repo = (
            os.environ.get("REPO_NAME", "cdis-manifest") if repo == None else repo
        )
        self.token = os.environ.get("GITHUB_TOKEN", "MEH-123").strip()

    def get_github_client(self):
        """
     return a github client object that can instrument a given repo
    """
        g = Github(self.token)
        org = g.get_organization(self.org)
        try:
            repo = org.get_repo(self.repo)
        except Exception as e:
            raise Exception(
                "Could not get remote repositiory {}: {}".format(self.repo, e)
            )

        return repo

    def clone_repo(self, github_client, repo_name, workspace):
        """
     clone a repo into the local workspace
    """
        creds = pygit2.UserPass(self.username, self.token)
        callbacks = RemoteCallbacks(creds, None)
        cloned_repo = pygit2.clone_repository(
            github_client.clone_url,
            workspace + "/{}".format(repo_name),
            callbacks=callbacks,
        )
        return cloned_repo

    def cut_new_branch(self, github_client, branch_name):
        source_branch = "master"
        target_branch = branch_name
        sb = github_client.get_branch(source_branch)
        print(sb)
        git_ref = github_client.create_git_ref(
            ref="refs/heads/" + target_branch, sha=sb.commit.sha
        )
        logging.info(
            "new branch [{}] has been created successfully (ref: {})".format(
                branch_name, str(git_ref)
            )
        )
        return git_ref

    def create_pull_request_user_yaml(
        self, github_client, user_yaml, target_user_yaml_path, pr_title, branch_name
    ):
        # add user.yaml file to the remote branch
        logging.debug("adding {} to branch {}".format(user_yaml, branch_name))
        copy_commit = "replicating {} into prod env.".format(user_yaml)
        user_yaml_file = open(user_yaml, "rb")
        data = user_yaml_file.read()
        file_contents = github_client.get_contents(
            "{}/user.yaml".format(target_user_yaml_path), branch_name
        )
        logging.debug("branch_name: {}".format(branch_name))
        github_client.update_file(
            "{}/user.yaml".format(target_user_yaml_path),
            copy_commit,
            data,
            file_contents.sha,
            branch=branch_name,
        )

        # finally, create Pull Request
        the_pr = github_client.create_pull(
            title=pr_title, body=copy_commit, head=branch_name, base="master"
        )
        the_pr.add_to_labels("automerge")

    def create_pull_request_release_notes(
        self,
        github_client,
        year,
        month,
        release_files,
        pr_title,
        commit_msg,
        branch_name,
    ):
        # add all files to the remote branch
        for f in release_files:
            logging.debug("adding {} to branch {}".format(f, branch_name))
            copy_commit = "adding {} as part of the release artifacts".format(f)
            input_file = open(f, "rb")
            data = input_file.read()
            logging.debug("branch_name: {}".format(branch_name))
            github_client.create_file(
                "releases/{}/{}/".format(year, month) + f,
                copy_commit,
                data,
                branch=branch_name,
            )

        # finally, create Pull Request
        the_pr = github_client.create_pull(
            title=pr_title, body=commit_msg, head=branch_name, base="master"
        )
        the_pr.add_to_labels("automerge")
        the_pr.add_to_labels("doc-only")

    def create_pull_request_apply(
        self,
        github_client,
        version,
        tgtEnv,
        modified_files,
        pr_title,
        commit_msg,
        branch_name,
    ):
        # add all files to the remote branch
        for f in modified_files:
            logging.debug("adding {} to branch {}".format(f, branch_name))
            copy_commit = "apply version {} to {}".format(version, tgtEnv.name)
            file_contents = github_client.get_contents(
                "{}/".format(tgtEnv.name) + f, branch_name
            )
            input_file = open("{}/".format(tgtEnv.full_path) + f, "rb")
            data = input_file.read()
            logging.debug("branch_name: {}".format(branch_name))
            github_client.update_file(
                "{}/".format(tgtEnv.name) + f,
                copy_commit,
                data,
                file_contents.sha,
                branch=branch_name,
            )

        # finally, create Pull Request
        the_pr = github_client.create_pull(
            title=pr_title, body=commit_msg, head=branch_name, base="master"
        )
        the_pr.add_to_labels("automerge")

    def create_pull_request_copy(
        self, github_client, tgtEnv, modified_files, pr_title, commit_msg, branch_name
    ):
        # add all files to the remote branch
        for f in modified_files:
            logging.debug("adding {} to branch {}".format(f, branch_name))
            copy_commit = "copying {} to {}".format(f, tgtEnv.name)
            input_file = open("{}/".format(tgtEnv.full_path) + f, "rb")
            data = input_file.read()
            logging.debug("branch_name: {}".format(branch_name))
            try:
                file_contents = github_client.get_contents(
                    "{}/".format(tgtEnv.name) + f, branch_name
                )
            except UnknownObjectException as e:
                logging.debug(
                    "{} has occurred, likely because file not found in remote, creating file..".format(
                        e
                    )
                )
                github_client.create_file(
                    "{}/".format(tgtEnv.name) + f, copy_commit, data, branch=branch_name
                )
            else:
                github_client.update_file(
                    "{}/".format(tgtEnv.name) + f,
                    copy_commit,
                    data,
                    file_contents.sha,
                    branch=branch_name,
                )

        # finally, create Pull Request
        github_client.create_pull(
            title=pr_title, body=commit_msg, head=branch_name, base="master"
        )
