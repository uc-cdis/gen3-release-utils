from github import Github
from git import Repo
import argparse
import os
from os import path
import re
import sys
import shutil
from shutil import copytree, Error
import logging
import json
import datetime

# Debugging:
# $ export LOGLEVEL=DEBUG

# how to run:
# $ python environments_config_manager.py apply -v 2020.04 -e ~/workspace/cdis-manifest/gen3.datastage.io
# or
# $ python environments_config_manager.py copy -s ~/workspace/cdis-manifest/staging.datastage.io -e ~/workspace/cdis-manifest/gen3.datastage.io

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger(__name__)

class GithubLib():
#  def __init__(self, org='uc-cdis', repo='cdis-manifest', token=os.environ['GITHUB_TOKEN'].strip()):
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
    return github_client.create_git_ref(ref='refs/heads/' + target_branch, sha=sb.commit.sha)

  def create_pull_request(self, github_client, target_env, version, modified_files, pr_title, commit_msg, branch_name):
    environment_path_regex = re.search(r'(.*)\/(.*)', target_env)
    logging.debug('identifying repo directory and name of the environment: {}'.format(str(environment_path_regex)))
    repo_dir = environment_path_regex.group(1)
    name_of_environment = environment_path_regex.group(2)
    repo = Repo(repo_dir)
    # create local branch
    repo.git.checkout(b=branch_name)
    repo.git.add(modified_files)
    repo.index.commit(commit_msg)
    # push commit to remote branch
    repo.git.push('origin', branch_name)
    # finally, create Pull Request
    github_client.create_pull(title=pr_title, body=commit_msg, head=branch_name, base="master")


def make_parser():
    parser = argparse.ArgumentParser(
        description="Updating configuration for Gen3 environments",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""\
Utility to update the version of services or copy all the configuration from one source environment to a target environment.
The general syntax for this script is:

environments_config_manager <command> <args>
e.g., python environments_config_manager copy -s ~/workspace/cdis-manifest/staging.datastage.io -e ~/workspace/cdis-manifest/gen3.datastage.io 
You can also use optional arg: "-pr" to create pull requests automatically

The most commonly used commands are:
   apply    Applies a given version to all services declared in the environment's manifest.
            e.g. $ python environments_config_manager.py apply -v 2020.04 -e ~/workspace/cdis-manifest/gen3.datastage.io
            or
            e.g. $ python environments_config_manager.py apply -v 2020.04 -e ~/workspace/cdis-manifest/gen3.datastage.io -pr \"task(project): Apply Core Gen3 April release\"

   copy     Copies the entire set of configuration artifacts from a source environment to a target environment (keeping the environment-specific settings, e.g., hostname, vpc, k8s namespace, guppy ES index, etc.)
            e.g. $ python environments_config_manager copy -s ~/workspace/cdis-manifest/staging.datastage.io -e ~/workspace/cdis-manifest/gen3.datastage.io
""",
    )

    subparsers = parser.add_subparsers()

    parser_apply = subparsers.add_parser(
        "apply",
        description="Applies an arbitrary version to all services",
    )
    parser_apply.add_argument(
        "-v",
        "--version",
        dest="version",
        required=True,
        type=str,
        help="name of the branch or tag that represents a quay.io Docker image (e.g., 2020.04)",
    )
    parser_apply.add_argument(
        "-e",
        "--env",
        dest="env",
        required=True,
        type=str,
        help="name of the environment (e.g., ~/workspace/gitops-qa/qa-dcp.planx-pla.net)",
    )
    parser_apply.add_argument(
        "-pr",
        "--pull-request-title",
        dest="pr_title",
        required=False,
        type=str,
        help="triggers automation that creates a pull request on github and sets a title (e.g., chore(qa): Updating qa-dcp with release 2020.04)",
    )
    parser_apply.set_defaults(func=apply)

    parser_copy = subparsers.add_parser(
        "copy",
        description="Copies ALL artifacts from a given source environment to a target environment",
    )
    parser_copy.add_argument(
        "-s",
        "--source",
        dest="source",
        required=True,
        type=str,
        help="name of the source environment whose config will be copied over to the target environment (e.g., ~/workspace/cdis-manifest/preprod.gen3.biodatacatalyst.nhlbi.nih.gov)",
    )
    parser_copy.add_argument(
        "-e",
        "--env",
        dest="env",
        required=True,
        type=str,
        help="name of the target environment whose config will be modified once all the config from the source environment is copied over (e.g., ~/workspace/cdis-manifest/gen3.biodatacatalyst.nhlbi.nih.gov)",
    )    
    parser_copy.add_argument(
        "-pr",
        "--pull-request-title",
        dest="pr_title",
        required=False,
        type=str,
        help="triggers automation that creates a pull request on github and sets a title (e.g., task(dcf): Promote changes from staging to prod - Release q1 2020)",
    )
    parser_copy.set_defaults(func=copy)
    parser.set_defaults(func=apply)
    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()
    if len(args._get_kwargs()) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args.func(args)

def merge_json_file_with_stored_environment_params(dst_path, the_file, env_params):
  full_path_to_file = '{}/{}'.format(dst_path, the_file)
  logging.debug('merging stored data from [{}] into {}'.format(the_file, full_path_to_file))
  with open(full_path_to_file, 'r+') as f:
    json_file = json.loads(f.read())
    merged_json = {**json_file, **env_params}
    f.seek(0)
    f.write(json.dumps(merged_json, indent=2))
    f.truncate()

def save_blocks(block, env_params, json_block):
  print('block: {}'.format(block))
  if type(env_params[block]) is dict:
    for sub_block in env_params[block].keys():
      # if the value of a given key is a dict and it is declared in ENVIRONMENT_SPECIFIC_PARAMS
      # apply recursion to store these parameters
      save_blocks(sub_block, env_params[block], json_block[block])
  else:
    logging.debug('saving block [{}]. Here is the value from the file: {}'.format(block, json_block[block]))
    env_params[block] = json_block[block]

def load_environment_params(dst_path, the_file):
  logging.debug('storing info from: ' + the_file)
  with open('{}/{}'.format(dst_path, the_file), 'r') as f:
    json_file = json.loads(f.read())
    env_params = ENVIRONMENT_SPECIFIC_PARAMS[the_file]
    for block in dict.fromkeys(env_params.keys(),[]).keys():
      if block in json_file.keys():
        save_blocks(block, env_params, json_file)
      else:
        del env_params[block]
        logging.warn('block {} does not exist in json file {}, ignoring this block.'.format(block, the_file))
  return env_params


def recursive_copy(src, dst):
  os.chdir(src)
  for a_file in os.listdir():
    if a_file == 'README.md': continue
    logging.debug('copying file: {}'.format(a_file))
    if os.path.isdir(a_file):
      new_dst = os.path.join(dst, a_file)
      os.makedirs(new_dst, exist_ok=True)
      recursive_copy(os.path.abspath(a_file) + '/', new_dst)
    else:
      logging.debug('copying {} into {}'.format(a_file, dst))
      # files mapped in ENVIRONMENT_SPECIFIC_PARAMS need special treatment
      if a_file in ENVIRONMENT_SPECIFIC_PARAMS.keys():
        logging.debug('This file [{}] contains environment-specific \
parameters that need to be saved.'.format(a_file))
        # remember environment-specific information
        env_params = load_environment_params(dst, a_file)
        shutil.copy(src + a_file, dst)
        logging.debug('Stored parameters: {}'.format(env_params))
        # re-apply all the stored environment-specific params
        merge_json_file_with_stored_environment_params(dst, a_file, env_params)
      else:
        shutil.copy(src + a_file, dst)

def replace_all_versions(version, json_block):
  for svc in json_block:
    if svc not in SVCS_TO_IGNORE:
      logging.debug('applying version {} to {}'.format(version, svc))
      json_block[svc] = '{}:{}'.format(json_block[svc].split(':')[0], version)
  return json_block


def replace_on_path(version, json_block, path):
  if type(path) is list:
    # Hardcode index 0 for now as we only have a single sower job in the config
    # TODO: Iterate through sower jobs and replace versions accordingly
    replace_on_path(version, json_block[0], path[0])
  else:
    for sub_block, img_ref in path.items():
      logging.debug('replacing {} in {}'.format(img_ref, sub_block))
      json_block[sub_block][img_ref] = '{}:{}'.format(json_block[sub_block][img_ref].split(':')[0], version)
  return json_block


ENVIRONMENT_SPECIFIC_PARAMS = {
  'manifest.json': {
    'notes': [],
    'global': {
      'environment': '', # VPC
      'hostname': '',
      'revproxy_arn': '',
      'dictionary_url': '',
      'kube_bucket': '',
      'logs_bucket': '',
      'sync_from_dbgap': '',
      'useryaml_s3path': ''
    },
    'hatchery': {
      'user-namespace': '',
      'sidecar': {
        'env': {
          'NAMESPACE': '', # KUBE_NAMESPACE
          'HOSTNAME': ''
        }
      },
    },
    'scaling': {
      'fence': {
        'min': 0,
        'max': 0
      }
    }
  },
  'hatchery.json': {
    'user-namespace': '',
    'env': {
      'NAMESPACE': '', # KUBE_NAMESPACE
      'HOSTNAME': ''
    },
  }
}

SVCS_TO_IGNORE = [
  'aws-es-proxy',
  'fluentd',
  'ambassador',
  'nb2'
]

BLOCKS_TO_UPDATE = {
  'manifest.json': {
    'versions': '*',
    'sower': [
        {
          'container': 'image'
        },
    ],
    'ssjdispatcher': {
      'job_images': 'indexing'
    },
    'hatchery': {
      'sidecar': 'image'
    }
  },
  'manifests/hatchery/hatchery.json': {
    'root': {
      'sidecar': 'image'
    }
  }
}

def apply(args):
    version = args.version
    target_env = args.env
    pr_title = args.pr_title
    logging.debug("version: {}".format(version))
    logging.debug("target_env: {}".format(target_env))
    logging.debug("pr_title: {}".format(pr_title))

    modified_files = []
    new_branch_ref = None
    branch_name = None

    # TODO: Refactor this function and break it down into smaller chunks
    for config_file_name in BLOCKS_TO_UPDATE.keys():
      if path.isfile('{}/{}'.format(target_env, config_file_name)):
        # Cut a new brach if the --pull-request-title flag is in place
        # create the branch only once
        if pr_title and new_branch_ref == None:
          # TODO: pick manifest repo from --env argument (gitops-qa or cdis-manifest)
          # Hardcoding cdis-manifest for now
          ts = datetime.datetime.now().timestamp()
          branch_name = 'chore/apply_{}_{}'.format(version.replace('.', ''), str(ts).split('.')[0])
          github_lib = GithubLib()
          github_client = github_lib.get_github_client()
          new_branch_ref = github_lib.cut_new_branch(github_client, branch_name)
          logging.info('new branch [{}] has been created successfully (ref: {})'.format(branch_name, str(new_branch_ref)))
        full_file_name = '{}/{}'.format(target_env, config_file_name)
        with open(full_file_name, 'r+') as config_file:
          json_file = json.loads(config_file.read())
          for block in list(BLOCKS_TO_UPDATE[config_file_name].keys()):
            if block in json_file or block == 'root':
              if block == 'versions':
                logging.debug('updating versions block from {}'.format(config_file_name))
                json_file[block] = replace_all_versions(version, json_file[block])
              else:
                logging.debug('updating {} block from {}'.format(block, '{}.json'.format(config_file_name)))
                json_block = json_file[block] if block != 'root' else json_file
                json_block = replace_on_path(version, json_block, BLOCKS_TO_UPDATE[config_file_name][block])
          config_file.seek(0)
          config_file.write(json.dumps(json_file, indent=2))
          config_file.truncate()
        modified_files.append(full_file_name)
    # If PR automation is enabled, add changes to the branch and create PR
    if new_branch_ref:
      logging.info('### Creating commit and pushing changes to the branch')
      commit_msg = 'Applying version {} to {}'.format(version, target_env)
      github_lib.create_pull_request(github_client, target_env, version, modified_files, pr_title, commit_msg, branch_name)
      logging.info('PR created successfully!')


def copy(args):
    source_env = args.source
    target_env = args.env
    logging.debug("source_env: {}".format(source_env))
    logging.debug("target_env: {}".format(target_env))
    # Check if paths exist
    if path.exists('{}'.format(source_env)) and path.exists('{}'.format(target_env)):
       try:
         # Cut a new brach if the --pull-request-title flag is in place
         
         recursive_copy('{}/'.format(source_env), target_env)
       except Error as err:
         logging.error('something went wrong while trying to copy the environment folder: {}'.format(err))
         sys.exit(1)
    else:
      logging.error('Invalid source and/or target environment. Double-check the paths and try again.')
      sys.exit(1)


if __name__ == "__main__":
    main()
