from gith.git import Git as Gh
from config.env import Env
from filesys import io
import argparse
import os
from os import path
import sys
import logging
import datetime

# Debugging:
# $ export LOGLEVEL=DEBUG

# how to run:
# $ python environments_config_manager.py apply -v 2020.04 -e ~/workspace/cdis-manifest/gen3.datastage.io
# or
# $ python environments_config_manager.py copy -s ~/workspace/cdis-manifest/staging.datastage.io -e ~/workspace/cdis-manifest/gen3.datastage.io

# To delete local garbage / experimental branches:
# % git branch | cat | grep apply | xargs -I {} git branch -D {}

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger(__name__)


def make_parser():
    parser = argparse.ArgumentParser(
        description="Updating configuration for Gen3 environments",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""\
Utility to update the version of services or copy all the configuration from one source environment to a target environment.
The general syntax for this script is:

environments_config_manager <command> <args>
e.g.: python environments_config_manager copy -s ~/workspace/cdis-manifest/staging.datastage.io -e ~/workspace/cdis-manifest/gen3.datastage.io 
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
        "apply", description="Applies an arbitrary version to all services",
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
        "-o",
        "--override",
        dest="override",
        required=False,
        type=str,
        default="{}",
        help="overrides versions as specified in a json-like format e.g., {'ambassador':'1.4.2'}",
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


def apply(args):
    version = args.version
    override = args.override
    target_env = args.env
    pr_title = args.pr_title
    logging.debug("version: {}".format(version))
    logging.debug("override: {}".format(override))
    logging.debug("target_env: {}".format(target_env))
    logging.debug("pr_title: {}".format(pr_title))

    # Create Environment Config object
    e = Env(target_env)

    modified_files = apply_version_to_environment(version, override, e)

    # Cut a new brach if the --pull-request-title flag is in place
    if pr_title and len(modified_files) > 0:
        ts = str(datetime.datetime.now().timestamp()).split(".")[0]
        branch_name = "chore/apply_{}_to_{}_{}".format(
            version.replace(".", ""), e.name.replace(".", "_"), ts
        )
        repo_name = os.path.basename(e.repo_dir)
        logging.debug("creating github client obj with repo={}".format(repo_name))
        gh = Gh(repo=repo_name)
        gh_client = gh.get_github_client()

        # create new remote branch
        new_branch_ref = gh.cut_new_branch(gh_client, branch_name)

        # create local branch, commit, push and create pull request
        commit_msg = "Applying version {} to {}".format(version, e.name)
        gh.create_pull_request_apply(
            gh_client, version, e, modified_files, pr_title, commit_msg, branch_name
        )
        logging.info("PR created successfully!")
        # TODO: Switch local branch to master


def apply_version_to_environment(version, override, e):
    modified_files = []
    for manifest_file_name in e.BLOCKS_TO_UPDATE.keys():
        manifest = "{}/{}/{}".format(e.repo_dir, e.name, manifest_file_name)
        if path.exists(manifest):
            current_md5, current_json = io.read_manifest(manifest)

            logging.debug("looking for versions to be replaced in {}".format(manifest))
            json_with_version = e.find_and_replace(
                version, override, manifest_file_name, current_json
            )

            new_md5 = io.write_into_manifest(manifest, json_with_version)

            if current_md5 != new_md5:
                modified_files.append(manifest)
        else:
            logging.warn(
                "environment [{}] does not contain the manifest file {}".format(
                    e.name, manifest
                )
            )

    # keep only relative paths (base_path = workspace)
    base_path = e.full_path
    logging.debug("base_path: {}".format(base_path))
    # remove base_path (keep only the files)
    modified_files = list(
        map(lambda f: f.replace(base_path, "").strip("/"), modified_files)
    )
    logging.debug("modified files: {}".format(modified_files))

    return modified_files


def copy(args):
    source_env = args.source
    target_env = args.env
    pr_title = args.pr_title
    logging.debug("source_env: {}".format(source_env))
    logging.debug("target_env: {}".format(target_env))
    logging.debug("pr_title: {}".format(pr_title))

    # Create Environment Config objects
    srcEnv = Env(source_env)
    tgtEnv = Env(target_env)

    modified_files = copy_all_files(srcEnv, tgtEnv)

    logging.debug("num of modified_files: {}".format(len(modified_files)))
    # Cut a new brach if the --pull-request-title flag is in place
    if pr_title and len(modified_files) > 0:
        ts = str(datetime.datetime.now().timestamp()).split(".")[0]
        branch_name = "chore/promote_{}_{}".format(srcEnv.name.replace(".", "_"), ts)
        repo_name = os.path.basename(tgtEnv.repo_dir)
        logging.debug("creating github client obj with repo={}".format(repo_name))
        gh = Gh(repo=repo_name)
        gh_client = gh.get_github_client()

        # create new remote branch
        new_branch_ref = gh.cut_new_branch(gh_client, branch_name)

        # create commit, push files to remote branch and create pull request
        commit_msg = "copying files from {} to {}".format(srcEnv.name, tgtEnv.name)
        gh.create_pull_request_copy(
            gh_client, srcEnv, tgtEnv, modified_files, pr_title, commit_msg, branch_name
        )
        logging.info("PR created successfully!")
        # TODO: Switch local branch to master


def copy_all_files(srcEnv, tgtEnv):
    # Check if paths exist
    if path.exists(srcEnv.full_path) and path.exists(tgtEnv.full_path):
        try:
            # copy all the files from the source environment folder
            # and re-apply the environment-specific parameters
            copied_files = io.recursive_copy(
                [], srcEnv, tgtEnv, srcEnv.full_path, tgtEnv.full_path
            )
            # keep only relative paths (base_path = workspace)
            base_path = tgtEnv.full_path
            logging.debug("base_path: {}".format(base_path))
            # remove base_path (keep only the files)
            copied_files = list(
                map(lambda f: f.replace(base_path, "").strip("/"), copied_files)
            )
            logging.debug("copied files: {}".format(copied_files))
            return copied_files
        except Exception as err:
            raise Exception(
                "something went wrong while trying to copy the environment folder: {}".format(
                    err
                )
            )

    else:
        raise NameError(
            "Invalid source and/or target environment.Source entered: [{}], target entered: [{}]. \
             Double-check the paths and try again.".format(srcEnv.full_path, tgtEnv.full_path)
        )


if __name__ == "__main__":
    main()
