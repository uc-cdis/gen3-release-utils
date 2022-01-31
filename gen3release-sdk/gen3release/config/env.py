import re
import os
import logging
import traceback
import json
import ast

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger(__name__)


class Env:
    def __init__(self, path_to_env_folder):
        """
        Creates an EnvironmentConfig object to store information related to its folder path and the name of the environment.
        This class also contains helper methods to facilitate the manipulation of config data.
        """
        self.environment_specific_params = {
            # We use dummy values in case one of the env-specifc params in target is empty
            "manifest.json": {
                "notes": "GEN3_RELEASE_SDK_PLACEHOLDER",
                "global": {
                    "environment": "GEN3_RELEASE_SDK_PLACEHOLDER",  # VPC
                    "hostname": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    "revproxy_arn": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    "kube_bucket": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    "logs_bucket": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    "sync_from_dbgap": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    "useryaml_s3path": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    "dd_enabled": "GEN3_RELEASE_SDK_PLACEHOLDER",
                },
                "hatchery": {
                    "user-namespace": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    "sidecar": {
                        "env": {
                            "NAMESPACE": "GEN3_RELEASE_SDK_PLACEHOLDER",
                            "HOSTNAME": "GEN3_RELEASE_SDK_PLACEHOLDER",
                        }
                    },  # KUBE_NAMESPACE
                },
                "scaling": {},
            },
            "hatchery.json": {
                "user-namespace": "GEN3_RELEASE_SDK_PLACEHOLDER",
                "env": {
                    "NAMESPACE": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    "HOSTNAME": "GEN3_RELEASE_SDK_PLACEHOLDER",
                },  # KUBE_NAMESPACE
                "sidecar": {
                    "env": {
                        "NAMESPACE": "GEN3_RELEASE_SDK_PLACEHOLDER",
                        "HOSTNAME": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    }
                },
            },
            "gitops.json": {
                "gaTrackingId": "GEN3_RELEASE_SDK_PLACEHOLDER",
                "dataExplorerConfig": {
                    "terraExportURL": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    "sevenBridgesExportURL": "GEN3_RELEASE_SDK_PLACEHOLDER",
                },
                "fileExplorerConfig": {
                    "terraExportURL": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    "sevenBridgesExportURL": "GEN3_RELEASE_SDK_PLACEHOLDER",
                },
                "components": {
                    "login": {
                        "title": "GEN3_RELEASE_SDK_PLACEHOLDER",
                    },
                },
            },
            "fence-config-public.yaml": {
                "BASE_URL": "GEN3_RELEASE_SDK_PLACEHOLDER",
                "S3_BUCKETS": {},
                "DATA_UPLOAD_BUCKET": "GEN3_RELEASE_SDK_PLACEHOLDER",
                "GOOGLE_GROUP_PREFIX": "GEN3_RELEASE_SDK_PLACEHOLDER",
                "GOOGLE_SERVICE_ACCOUNT_PREFIX": "GEN3_RELEASE_SDK_PLACEHOLDER",
                "LOGIN_REDIRECT_WHITELIST": "GEN3_RELEASE_SDK_PLACEHOLDER",
            },
        }

        self.files_to_ignore = ["fence-config-public.yaml"]

        self.params_to_set = {
            "manifest.json": {"guppy": {"indices": [], "config_index": ""}},
            "etlMapping.yaml": {"mappings": []},
        }

        self.svcs_to_ignore = [
            "arranger",
            "arranger-dashboard",
            "arranger-adminapi",
            "augur",
            "auspice",
            "aws-es-proxy",
            "covid19-etl",
            "covid19-notebook-etl",
            "covid19-bayes",
            "fluentd",
            "ambassador",
            "nb2",
            "jupyterhub",
            "jenkins",
            "ohdsi-atlas",
            "ohdsi-webapi",
        ]

        self.blocks_to_update = {
            "manifest.json": {
                "versions": "*",
                "sower": [{"container": "image"}],
                "jupyterhub": {"root": "sidecar"},
                "ssjdispatcher": {"job_images": "indexing"},
                "hatchery": {"sidecar": "image"},
            },
            "manifests/hatchery/hatchery.json": {"root": {"sidecar": "image"}},
        }

        path_to_env_folder = os.path.abspath(path_to_env_folder)

        if "/" == path_to_env_folder[-1]:
            path_to_env_folder = path_to_env_folder[:-1]

        logging.debug(
            "identifying repo directory and name of the environment: {}".format(
                str(path_to_env_folder)
            )
        )
        pathsplits = path_to_env_folder.split("/")
        self.repo_dir = pathsplits[-2]
        self.name = pathsplits[-1]
        self.full_path = path_to_env_folder
        self.sower_jobs = []

    def load_sower_jobs(self, json_data):
        self.sower_jobs = json_data.get("sower", [])

    def _replace_one(self, version, key, json_block):
        if key in json_block:
            logging.debug(
                "applying version {} to key {} in block {}".format(
                    version, key, json_block
                )
            )
            json_block[key] = "{}:{}".format(json_block[key].split(":")[0], version)
        else:
            logging.warning(
                "nothing to replace here. The key [{}] was not found in this json block.".format(
                    key
                )
            )
        return json_block

    def _replace_all_versions(self, version, override, json_block):
        try:
            dict_override = ast.literal_eval(override)
        except:
            logging.debug("Malformed override json string passed - {}".format(override))
            dict_override = {}
        for svc in json_block:
            if "dashboard" not in json_block:
                self.svcs_to_ignore.append("dashboard")
            if svc not in self.svcs_to_ignore:
                logging.debug("applying version {} to {}".format(version, svc))
                json_block[svc] = "{}:{}".format(json_block[svc].split(":")[0], version)
        for svc in dict_override:
            logging.debug("applying version {} to {}".format(dict_override[svc], svc))
            json_block[svc] = dict_override[svc]
        return json_block

    def _replace_on_path(self, version, json_block, path):
        if type(path) is list and type(json_block) is list:
            for i in range(len(json_block)):
                self._replace_on_path(version, json_block[i], path[0])
        else:
            for sub_block, img_ref in path.items():
                logging.debug("replacing {} in {}".format(img_ref, sub_block))
                json_block[sub_block][img_ref] = "{}:{}".format(
                    json_block[sub_block][img_ref].split(":")[0], version
                )

        return json_block

    def find_and_replace(self, version, override, manifest_file_name, json):
        for block in list(self.blocks_to_update[manifest_file_name].keys()):
            logging.debug("block: {}".format(block))
            if block in json or block == "root":
                if block == "versions":
                    logging.debug(
                        "updating versions block from {}".format(manifest_file_name)
                    )
                    json[block] = self._replace_all_versions(
                        version, override, json[block]
                    )
                elif (
                    type(json.get(block)) == dict
                    and "root"
                    in self.blocks_to_update[manifest_file_name][block].keys()
                ):
                    logging.debug("updating one parameter from a root block")
                    the_key = self.blocks_to_update[manifest_file_name][block]["root"]
                    json[block] = self._replace_one(version, the_key, json[block])
                else:
                    logging.debug(
                        "updating {} block from {}".format(
                            block, "{}.json".format(manifest_file_name)
                        )
                    )
                    json_block = json[block] if block != "root" else json
                    json_block = self._replace_on_path(
                        version,
                        json_block,
                        self.blocks_to_update[manifest_file_name][block],
                    )
            else:
                logging.warning(
                    "block {} does not exist in {}".format(block, manifest_file_name)
                )
        return json

    def save_blocks(self, block, env_params, json_block):
        if not json_block:
            return
        # if value is empty dictionary - add copy_all to not recurse on dict when merging
        if not env_params[block] and isinstance(env_params[block], dict):
            env_params[block]["COPY_ALL"] = json_block.get(block)
        elif isinstance(env_params[block], dict):
            for sub_block in env_params[block].keys():
                # if the value of a given key is a dict and it is declared in environment_specific_params
                # apply recursion to store these parameters
                self.save_blocks(sub_block, env_params[block], json_block.get(block))
        else:
            logging.debug(
                "saving block [{}]. Here is the value from the file: {}".format(
                    block, json_block.get(block)
                )
            )
            env_params[block] = json_block.get(block)

    def load_environment_params(self, file_name, json_data):
        """Places environment specific values from target environment into  env object,
        removes fields from object not found in target and returns the dictionary with fields"""
        logging.debug("storing info from: " + file_name)
        try:
            env_params = self.environment_specific_params[file_name]
            for block in dict.fromkeys(env_params.keys(), []).keys():
                if block in json_data.keys():
                    self.save_blocks(block, env_params, json_data)

                else:
                    del env_params[block]
                    logging.warning(
                        "block {} does not exist in json file {}, ignoring this block.".format(
                            block, file_name
                        )
                    )
            return env_params
        except Exception as e:
            logging.error("failed to load parameters from {}.".format(file_name))
            traceback.print_exc()
