import argparse
import os
from os import path
import sys
import logging
import time

from gith.git import Git as Gh
from config.env import Env
from filesys import io_processing as py_io

# Debugging:
# $ export LOGLEVEL=DEBUG

# how to run:
# $ gen3release apply -v 2020.04 -e ~/workspace/cdis-manifest/gen3.datastage.io
# or
# $ gen3release copy -s ~/workspace/cdis-manifest/staging.datastage.io -e ~/workspace/cdis-manifest/gen3.datastage.io

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

gen3release <command> <args>
e.g.: gen3release copy -s ~/workspace/cdis-manifest/staging.datastage.io -e ~/workspace/cdis-manifest/gen3.datastage.io
You can also use optional arg: "-pr" to create pull requests automatically

The most commonly used commands are:
   apply    Applies a given version to all services declared in the environment's manifest.
            e.g. $ gen3release apply -v 2020.04 -e ~/workspace/cdis-manifest/gen3.datastage.io
            or
            e.g. $ gen3release apply -v 2020.04 -e ~/workspace/cdis-manifest/gen3.datastage.io -pr \"task(project): Apply Core Gen3 April release\"

   copy     Copies the entire set of configuration artifacts from a source environment to a target environment (keeping the environment-specific settings, e.g., hostname, vpc, k8s namespace, guppy ES index, etc.)
            e.g. $ gen3release copy -s ~/workspace/cdis-manifest/staging.datastage.io -e ~/workspace/cdis-manifest/gen3.datastage.io

   notes    Creates a pull request against a manifests repo storing release artifacts in a releases/<year>/<month> folder. It should store a general release manifest.json and the monthly release notes / markdown files.
            e.g. $ gen3release notes -v 2020.08 -f $SOME_FOLDER/gen3_release_notes.md $SOME_FOLDER/manifest.json

   users    Creates a pull request in a users repo to replicate all permissions (roles, policies, users, etc.) from the user.yaml configured against internalstaging or preprod environments to their correspondent prod user.yaml files. That should avoid discrepancies between preprod and prod environments and prevent issues related to lack of permissions.
            e.g. $ gen3release users -s commons-users/users/anvilinternalstaging/user.yaml -t commons-users/users/anvil/user.yaml
""",
    )

    subparsers = parser.add_subparsers()

    parser_apply = subparsers.add_parser(
        "apply", description="Applies an arbitrary version to all services"
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
    parser_apply.add_argument(
        "-l",
        "--label",
        nargs="*",
        dest="pr_labels",
        required=False,
        type=str,
        help="set one or more labels delimited by space to the pull request (e.g., gen3-release automerge)",
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

    parser_notes = subparsers.add_parser(
        "notes",
        description="Creates pull request containing the release notes and manifest.json files",
    )
    parser_notes.add_argument(
        "-v",
        "--version",
        dest="version",
        required=True,
        type=str,
        help="Release version (e.g., 2020.08)",
    )
    parser_notes.add_argument(
        "-f",
        "--files",
        nargs="+",
        dest="files",
        required=True,
        type=str,
        help="list of file paths containing the monthly release artifacts to be stored in a manifests repo (e.g., ~/gen3_release_notes.md ~/manifest.json ~/knownbugs.md)",
    )
    parser_notes.set_defaults(func=notes)

    parser_users = subparsers.add_parser(
        "users",
        description="Creates pull request to replica the contents of a preprod user.yaml to its corresponding prod user.yaml",
    )
    parser_users.add_argument(
        "-s",
        "--source",
        dest="source",
        required=True,
        type=str,
        help="Source path to preprod user.yaml (e.g., commons-users/users/datastageinternalstaging/user.yaml)",
    )
    parser_users.add_argument(
        "-t",
        "--target",
        dest="target",
        required=True,
        type=str,
        help="Target path to the prod user.yaml (e.g., datastage-users/users/stageprod/user.yaml)",
    )
    parser_users.set_defaults(func=users)

    parser.set_defaults(func=apply)
    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()
    if len(args._get_kwargs()) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args.func(args)


def users(args):
    src_user_yaml = args.source
    tgt_user_yaml = args.target
    logging.debug("src_user_yaml: {}".format(src_user_yaml))
    logging.debug("tgt_user_yaml: {}".format(tgt_user_yaml))

    workspace = os.getcwd()
    path_to_source_user_yaml_folder = os.path.abspath(src_user_yaml)
    path_to_target_user_yaml_folder = os.path.abspath(tgt_user_yaml)

    srcpathsplits = path_to_source_user_yaml_folder.split("/")
    tgtpathsplits = path_to_target_user_yaml_folder.split("/")
    src_repo_dir = srcpathsplits[-4]
    tgt_repo_dir = tgtpathsplits[-4]

    logging.info("src_repo_dir: {}".format(src_repo_dir))
    logging.info("tgt_repo_dir: {}".format(tgt_repo_dir))

    srcgh = Gh(repo=src_repo_dir)
    src_gh_client = srcgh.get_github_client()
    tgtgh = Gh(repo=tgt_repo_dir)
    tgt_gh_client = tgtgh.get_github_client()

    try:
        logging.debug("cloning src repo: {}".format(src_gh_client.clone_url))
        os.mkdir(workspace + "/source")
        src_user_yaml_repo = srcgh.clone_repo(
            src_gh_client, src_repo_dir, workspace + "/source"
        )
        logging.debug("cloning tgt repo: {}".format(tgt_gh_client.clone_url))
        os.mkdir(workspace + "/target")
        tgt_user_yaml_repo = tgtgh.clone_repo(
            tgt_gh_client, tgt_repo_dir, workspace + "/target"
        )
    except Exception as git_error:
        print("Something went wrong: {}".format(git_error))
        sys.exit(1)

    source_user_yaml_path = "{}/{}".format(srcpathsplits[-4], srcpathsplits[-2])
    target_user_yaml_path = "{}/{}".format(tgtpathsplits[-3], tgtpathsplits[-2])
    logging.debug("target_user_yaml_path: {}".format(target_user_yaml_path))
    replicating_msg = "Replicating user.yaml from {} to {}".format(
        path_to_source_user_yaml_folder, path_to_target_user_yaml_folder
    )
    logging.debug(replicating_msg)
    pr_title = "chore(release): Replicating user.yaml from {}".format(
        source_user_yaml_path
    )
    ts = str(time.time()).split(".")[0]
    branch_name = "chore/replicate_user_yaml_from_{}_{}".format(
        src_user_yaml.replace("/", "_"), ts
    )

    # create new remote branch
    new_branch_ref = tgtgh.cut_new_branch(tgt_gh_client, branch_name)
    logging.info(f"branch name is {branch_name}")

    tgtgh.create_pull_request_user_yaml(
        tgt_gh_client,
        "source/" + src_user_yaml,
        target_user_yaml_path,
        pr_title,
        branch_name,
    )
    logging.info("PR created successfully!")


def notes(args):
    version = args.version
    files = args.files
    logging.debug("version: {}".format(version))
    logging.debug("files: {}".format(files))

    year = version.split(".")[0]
    month = version.split(".")[1]

    pr_title = "doc(qa) adding release notes for {}".format(version)

    ts = str(time.time()).split(".")[0]
    branch_name = "doc/release_artifacts_{}".format(ts)
    repo_name = "cdis-manifest"
    logging.debug("creating github client obj with repo={}".format(repo_name))
    gh = Gh(repo=repo_name)
    gh_client = gh.get_github_client()

    # create new remote branch
    new_branch_ref = gh.cut_new_branch(gh_client, branch_name)

    # create local branch, commit, push and create pull request
    commit_msg = "Storing release artifacts for version {}".format(version)
    gh.create_pull_request_release_notes(
        gh_client, year, month, files, pr_title, commit_msg, branch_name
    )
    logging.info("PR created successfully!")


def apply(args):
    version = args.version
    override = args.override
    target_env = args.env
    pr_title = args.pr_title
    pr_labels = args.pr_labels
    logging.debug("version: {}".format(version))
    logging.debug("override: {}".format(override))
    logging.debug("target_env: {}".format(target_env))
    logging.debug("pr_title: {}".format(pr_title))
    logging.debug("pr_title: {}".format(pr_labels))

    # Create Environment Config object
    e = Env(target_env)

    modified_files = apply_version_to_environment(version, override, e)

    # Cut a new brach if the --pull-request-title flag is in place
    if pr_title and len(modified_files) > 0:
        ts = str(time.time()).split(".")[0]
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
            gh_client,
            version,
            e,
            modified_files,
            pr_title,
            pr_labels,
            commit_msg,
            branch_name,
        )
        logging.info("PR created successfully!")
        # TODO: Switch local branch to master


def apply_version_to_environment(version, override, e):
    modified_files = []
    for manifest_file_name in e.blocks_to_update.keys():
        manifest = "{}/{}".format(e.full_path, manifest_file_name)
        if path.exists(manifest):
            current_md5, current_json = py_io.read_manifest(manifest)

            logging.debug("looking for versions to be replaced in {}".format(manifest))
            json_with_version = e.find_and_replace(
                version, override, manifest_file_name, current_json
            )

            new_md5 = py_io.write_into_manifest(manifest, json_with_version)
            logging.debug(f"new{new_md5} old {current_md5}")

            if current_md5 != new_md5:
                modified_files.append(manifest)
        else:
            logging.warning(
                "environment [{}] does not contain the manifest file {}".format(
                    e.name, manifest
                )
            )
            sys.exit(1)

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
        ts = str(time.time()).split(".")[0]
        branch_name = "chore/promote_{}_{}".format(srcEnv.name.replace(".", "_"), ts)
        repo_name = os.path.basename(tgtEnv.repo_dir)
        logging.debug("creating github client obj with repo={}".format(repo_name))
        gh = Gh(repo=repo_name)
        gh_client = gh.get_github_client()
        logging.info(f"Created a github object {gh_client}")

        # create new remote branch
        new_branch_ref = gh.cut_new_branch(gh_client, branch_name)
        logging.info(f"branch name is {branch_name}")

        # create commit, push files to remote branch and create pull request
        commit_msg = "copying files from {} to {}".format(srcEnv.name, tgtEnv.name)

        gh.create_pull_request_copy(
            gh_client, tgtEnv, modified_files, pr_title, commit_msg, branch_name
        )
        logging.info(f"{modified_files}, {commit_msg}")
        logging.info("PR created successfully!")
        # TODO: Switch local branch to master


def copy_all_files(srcEnv, tgtEnv):
    # Check if paths exist
    if path.exists(srcEnv.full_path) and path.exists(tgtEnv.full_path):
        try:
            # copy all the files from the source environment folder
            # and re-apply the environment-specific parameters
            files_copied = py_io.recursive_copy(
                srcEnv, tgtEnv, srcEnv.full_path, tgtEnv.full_path
            )
            # keep only relative paths (base_path = workspace)
            base_path = srcEnv.full_path
            logging.debug("base_path: {}".format(base_path))
            # remove base_path (keep only the files)
            copied_files = [
                f.replace(base_path, "").strip("/")
                for f, v in files_copied.items()
                if v
            ]

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
             Double-check the paths and try again.".format(
                srcEnv.full_path, tgtEnv.full_path
            )
        )


if __name__ == "__main__":
    main()
