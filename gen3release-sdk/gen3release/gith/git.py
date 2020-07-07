from github import Github
import os
import logging
from github.GithubException import UnknownObjectException

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger(__name__)


class Git:
    def __init__(
        self,
        org="uc-cdis",
        repo="cdis-manifest",
        token=os.environ["GITHUB_TOKEN"].strip(),
    ):
        """
     Creates a Github utils object to perform various operations against the uc-cdis repos and its branches, pull requests, etc.
    """
        self.org = org
        self.repo = repo
        self.token = token

    def get_github_client(self):
        """
     return a github client object that can instrument a given repo
    """
        g = Github(self.token)
        org = g.get_organization(self.org)
        try:
            repo = org.get_repo(self.repo)
        except Exception as e:
            raise Exception("Could not get remote repositiory {}: {}".format(repo, e))

        return repo

    def cut_new_branch(self, github_client, branch_name):
        source_branch = "master"
        target_branch = branch_name
        sb = github_client.get_branch(source_branch)
        git_ref = github_client.create_git_ref(
            ref="refs/heads/" + target_branch, sha=sb.commit.sha
        )
        logging.info(
            "new branch [{}] has been created successfully (ref: {})".format(
                branch_name, str(git_ref)
            )
        )
        return git_ref

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
        self,
        github_client,
        srcEnv,
        tgtEnv,
        modified_files,
        pr_title,
        commit_msg,
        branch_name,
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
                github_client.update_file(
                    "{}/".format(tgtEnv.name) + f,
                    copy_commit,
                    data,
                    file_contents.sha,
                    branch=branch_name,
                )
            except UnknownObjectException as e:
                logging.DEBUG(
                    "{} has occured, likely because file not found in remote, creating file..".format(
                        e
                    )
                )
                github_client.create_file(
                    "{}/".format(tgtEnv.name) + f, copy_commit, data, branch=branch_name
                )

        # finally, create Pull Request
        github_client.create_pull(
            title=pr_title, body=commit_msg, head=branch_name, base="master"
        )
