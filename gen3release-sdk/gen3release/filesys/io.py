import hashlib
import shutil
from config.env import Env
from shutil import copytree, Error
import logging
import json
import os
import traceback
from ruamel.yaml import YAML
from os import path

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger(__name__)


def read_manifest(manifest):
    with open(manifest, "r") as m:
        contents = m.read()
        return hashlib.md5(contents.encode("utf-8")), json.loads(contents)


def merge(source, destination):
    "Recursively merges dictionary source into dictionary destination" ""
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination


def write_into_manifest(manifest, json_with_changes):
    with open(manifest, "r+") as m:
        m.seek(0)
        m.write(json.dumps(json_with_changes, indent=2))
        m.truncate()
        return hashlib.md5(m.read().encode("utf-8"))


def merge_json_file_with_stored_environment_params(
    dst_path, the_file, env_params, srcEnc, tgtEnv
):
    full_path_to_file = "{}/{}".format(dst_path, the_file)
    logging.debug(
        "merging stored data from [{}] into {}".format(the_file, full_path_to_file)
    )

    with open(full_path_to_file, "r+") as f:
        json_file = json.loads(f.read())
        if the_file == "manifest.json":
            json_file = remove_superfluous_resources(
                json_file,
                srcEnc.ENVIRONMENT_SPECIFIC_PARAMS,
                tgtEnv.ENVIRONMENT_SPECIFIC_PARAMS,
            )
            tgtEnv.set_params(the_file, json_file)
            target_guppy = tgtEnv.PARAMS_TO_SET[the_file]["guppy"]
            json_guppy = json_file.get("guppy")
            if json_guppy:
                for i in range(len(json_guppy["indices"])):
                    json_guppy["indices"][i]["index"] = target_guppy["indices"][i][
                        "index"
                    ]
                if target_guppy["config_index"]:
                    json_guppy["config_index"] = target_guppy["config_index"]
        merged_json = merge(env_params, json_file)

        f.seek(0)
        f.write(json.dumps(merged_json, indent=2))
        f.truncate()


def handle_guppy(mani_json, srcEnv, tgtEnv):
    """Changes the Guppy index fields to be of the form <commonsname>_<type>"""
    gp = mani_json.get("guppy")
    if not gp:
        return mani_json
    indices = gp["indices"]
    for i in indices:
        i["index"] = tgtEnv.name + "_" + i["type"]
    gp["config_index"] = tgtEnv.name + "_" + "array-config"
    return mani_json


def remove_superfluous_resources(mani_json, srcEnv, tgtEnv):
    """Removes resources added to target environment by source 
    environment not found in original target environment"""
    superflous_resources = []

    srcnames = [x["name"] for x in srcEnv["manifest.json"]["sower"]]
    trgnames = [x["name"] for x in tgtEnv["manifest.json"]["sower"]]
    for name in srcnames:
        if name not in trgnames:
            superflous_resources.append(name)
    logging.debug(
        "Original target environment does not have {}, removing from target".format(
            superflous_resources
        )
    )
    mani_json["sower"] = [
        x for x in mani_json["sower"] if x["name"] not in superflous_resources
    ]
    return mani_json


def recursive_copy(copied_files, srcEnv, tgtEnv, src, dst):
    os.chdir(src)
    curr_dir = os.getcwd()
    logging.debug("current_dir: {}".format(curr_dir))
    try:
        for a_file in os.listdir():
            if a_file == "README.md":
                continue
            logging.debug("copying file: {}".format(("{}/".format(curr_dir) + a_file)))
            if os.path.isdir("{}/".format(os.getcwd()) + a_file):
                logging.debug(
                    "this file {} is a directory. Stepping into it".format(a_file)
                )
                new_dst = os.path.join(dst, a_file)
                os.makedirs(new_dst, exist_ok=True)
                curr_src = os.path.abspath(a_file)
                recursive_copy(copied_files, srcEnv, tgtEnv, curr_src, new_dst)
                logging.debug("finished recursion on folder: {}".format(a_file))
                os.chdir(os.path.abspath(".."))
            else:
                logging.debug("copying {} into {}".format(a_file, dst))
                # files mapped in ENVIRONMENT_SPECIFIC_PARAMS need special treatment
                if path.exists("{}/{}".format(dst, a_file)):
                    if a_file in tgtEnv.ENVIRONMENT_SPECIFIC_PARAMS.keys():
                        logging.debug(
                            "This file [{}] contains environment-specific parameters that need to be saved.".format(
                                a_file
                            )
                        )
                        # remember environment-specific information
                        json_file = None
                        with open("{}/{}".format(dst, a_file), "r") as j:
                            json_file = json.loads(j.read())
                        env_params = tgtEnv.load_environment_params(a_file, json_file)
                        logging.debug("Stored parameters: {}".format(env_params))

                        shutil.copy("{}/".format(curr_dir) + a_file, dst)

                        # re-apply all the stored environment-specific params
                        merge_json_file_with_stored_environment_params(
                            dst, a_file, env_params, srcEnv, tgtEnv
                        )
                    elif a_file == "etlMapping.yaml":
                        full_path_to_file = "{}/{}".format(dst, a_file)
                        with open(full_path_to_file, "r+") as f:
                            yaml = YAML(typ="safe")
                            yam_file = yaml.load(f)
                            tgtEnv.set_params(a_file, yam_file)
                            target_mappings = tgtEnv.PARAMS_TO_SET[a_file]["mappings"]
                            yam_mappings = yam_file["mappings"]
                            for i in range(len(target_mappings)):
                                yam_mappings[i]["name"] = target_mappings[i]["name"]

                            yaml = YAML()
                            f.seek(0)
                            yaml.default_flow_style = False
                            yaml.dump(yam_file, f)
                            f.truncate()

                else:
                    logging.debug(
                        "{} not found in target env, adding from source env".format(
                            a_file
                        )
                    )
                    shutil.copy("{}/".format(curr_dir) + a_file, dst)
                copied_files.append("{}/".format(dst) + a_file)
        return copied_files
    except Exception as e:
        logging.error(
            "something went wrong during the recursive copy of [{}] into [{}]".format(
                srcEnv.name, tgtEnv.name
            )
        )
        traceback.print_exc()
