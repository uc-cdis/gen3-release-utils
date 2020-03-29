import argparse
import os
import os.path
from os import path
import re
import sys
import logging
import json

# Debugging:
# $ export LOGLEVEL=DEBUG

# how to run:
# $ python environments_config_manager.py apply -v 2020.04 -e ~/workspace/cdis-manifest/gen3.datastage.io
# or
# $ python environments_config_manager.py copy -s ~/workspace/cdis-manifest/staging.datastage.io -e ~/workspace/cdis-manifest/gen3.datastage.io

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

def make_parser():
    parser = argparse.ArgumentParser(
        description="Updating configuration for Gen3 environments",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""\
Utility to update the version of services or copy all the configuration from one source environment to a target environment.
The general syntax for this script is:

environments_config_manager <command> <args>
e.g., python environments_config_manager copy -s ~/workspace/cdis-manifest/staging.datastage.io -e ~/workspace/cdis-manifest/gen3.datastage.io

The most commonly used commands are:
   apply    Applies a given version to all services (or just a specific set) declared in the environment's manifest.
            e.g. $ python environments_config_manager.py apply -v 2020.04 -e ~/workspace/cdis-manifest/gen3.datastage.io
            or
            $ python environments_config_manager.py apply -v 2020.05 -e ~/workspace/gitops-qa/qa-dcp.datastage.io -k gen3fuse,indexd,index
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
        "-k",
        "--keys",
        dest="keys",
        required=False,
        type=str,
        help="comma separated list of services (json keys) to which the version should be applied (e.g., gen3fuse,indexd,index)",
    )

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

    parser.set_defaults(func=apply)
    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()
    if len(args._get_kwargs()) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args.func(args)

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


SVCS_TO_IGNORE = [
  'aws-es-proxy',
  'fluentd',
  'ambassador',
  'nb2'
]

BLOCKS_TO_UPDATE = {
  'manifest': {
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
  'manifests/hatchery/hatchery': {
    'root': {
      'sidecar': 'image'
    }
  }
}

def apply(args):
    version = args.version
    target_env = args.env
    logging.debug("version: {}".format(version))
    logging.debug("target_env: {}".format(target_env))

    for config_file_name in BLOCKS_TO_UPDATE.keys():
      if path.isfile('{}/{}.json'.format(target_env, config_file_name)):
        with open('{}/{}.json'.format(target_env, config_file_name), 'r+') as config_file:
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


def copy(args):
    source_env = args.source
    target_env = args.env
    logging.debug("source_env: {}".format(source_env))
    logging.debug("target_env: {}".format(target_env))

if __name__ == "__main__":
    main()
