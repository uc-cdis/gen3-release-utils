from github import Github
from git import Repo
import os
import logging


LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger(__name__)

class Git():
  def __init__(self, org='uc-cdis', repo='cdis-manifest', token=os.environ['GITHUB_TOKEN'].strip()):
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
    repo = org.get_repo(self.repo)
    return repo

  def cut_new_branch(self, github_client, branch_name):
    source_branch = 'master'
    target_branch = branch_name
    sb = github_client.get_branch(source_branch)
    git_ref = github_client.create_git_ref(ref='refs/heads/' + target_branch, sha=sb.commit.sha)
    logging.info('new branch [{}] has been created successfully (ref: {})'.format(branch_name, str(git_ref)))
    return git_ref

  def create_pull_request(self, github_client, environment, modified_files, pr_title, commit_msg, branch_name):
    repo_dir = environment.repo_dir
    name_of_environment = environment.name
    repo = Repo(repo_dir)
    # create local branch
    repo.git.checkout(b=branch_name)
    repo.git.add(modified_files)
    repo.index.commit(commit_msg)
    # push commit to remote branch
    repo.git.push('origin', branch_name)
    # finally, create Pull Request
    github_client.create_pull(title=pr_title, body=commit_msg, head=branch_name, base="master")

