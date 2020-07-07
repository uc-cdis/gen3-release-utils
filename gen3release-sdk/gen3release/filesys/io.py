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


def validate_name(name):
    """Makes sure index names follow rules set in 
    https://www.elastic.co/guide/en/elasticsearch/reference/7.5/indices-create-index.html#indices-create-api-path-params"""
    BAD_CHARS = ["\\", "/", "*", "?", '"', "<", ">", "|", " ", ",", "#", ":"]
    BAD_START_CHARS = ["-", "_", "+"]
    BAD_NAMES = [".", ".."]
    if name in BAD_NAMES:
        raise NameError("The name {} is invalid".format(name))

    out_name = ""
    if name[0] in BAD_START_CHARS:
        name = name[1:]
    for c in name:
        if c in BAD_CHARS:
            continue
        out_name += c
    size = len(out_name.encode("utf-8"))
    if size > 255:
        raise NameError(
            "The name {} is {} bytes, but cannot exceed 255 bytes".format(
                out_name, size
            )
        )
    return out_name.lower()


def create_env_index_name(env_obj, the_file, data):
    params = env_obj.PARAMS_TO_SET[the_file]
    if the_file == "manifest.json":
        param_guppy = params["guppy"]
        file_guppy = data.get("guppy")
        if not file_guppy:
            return
        # Changes the Guppy index names to be of the form <commonsname>_<type>
        types_seen = {}
        for index in file_guppy.get("indices"):
            inx_type = index.get("type")
            if inx_type in types_seen.keys():
                types_seen[inx_type] += 1
                typename = inx_type + str(types_seen[inx_type])
            else:
                types_seen[inx_type] = 1
                typename = inx_type
            index_name = validate_name(env_obj.name + "_" + typename)
            param_guppy["indices"].append({"index": index_name})
        config_index = file_guppy.get("config_index")
        if config_index:
            param_guppy["config_index"] = env_obj.name + "_" + "array-config"
        
        for i in range(len(file_guppy["indices"])):
            file_guppy["indices"][i]["index"] = param_guppy["indices"][i]["index"]
        if param_guppy.get("config_index"):
            file_guppy["config_index"] = param_guppy["config_index"]

    elif the_file == "etlMapping.yaml":
        # Change name field to be of the form <commonsname>_<type>
        types_seen = {}
        for field in data["mappings"]:
            field_type = field.get("doc_type")
            if field_type in types_seen.keys():
                types_seen[field_type] += 1
                typename = field_type + str(types_seen[field_type])
            else:
                types_seen[field_type] = 1
                typename = field_type
            field_name = validate_name(env_obj.name + "_" + typename)
            params["mappings"].append({"name": field_name})
        target_mappings = env_obj.PARAMS_TO_SET[the_file]["mappings"]
        yam_mappings = data["mappings"]
        for i in range(len(target_mappings)):
            yam_mappings[i]["name"] = target_mappings[i]["name"]
    return data


def write_index_names(curr_dir, path, filename, env_obj):
    isyaml = filename.endswith("yaml")
    data = None
    full_path_to_target = "{}/{}".format(path, filename)
    if isyaml:
        shutil.copy("{}/".format(curr_dir) + filename, full_path_to_target)
        fd = open(full_path_to_target, "r+")
        yaml = YAML(typ="safe")
        data = yaml.load(fd)
    else:
        fd = open(full_path_to_target, "r+")
        data = json.loads(fd.read())
    create_env_index_name(env_obj, filename, data)
    fd.seek(0)
    if isyaml:
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(data, fd)
    else:
        fd.write(json.dumps(data, indent=2))
    fd.truncate()
    fd.close()


def store_environment_params(path, env_obj, filename):

    assert filename.endswith("json"), "Must be a json file"
    with open("{}/{}".format(path, filename), "r") as j:
        data = json.loads(j.read())
        env_obj.load_sower_jobs(data)
    return env_obj.load_environment_params(filename, data)


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
            json_file = remove_superfluous_sower_jobs(
                json_file, srcEnc.sower_jobs, tgtEnv.sower_jobs
            )
        merged_json = merge(env_params, json_file)

        f.seek(0)
        f.write(json.dumps(merged_json, indent=2))
        f.truncate()


def remove_superfluous_sower_jobs(mani_json, srcEnv, tgtEnv):
    """Removes sower jobs added to target environment by source 
    environment if job was not found in original target environment"""
    superflous_resources = []

    srcnames = [x["name"] for x in srcEnv]
    trgnames = [x["name"] for x in tgtEnv]
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
                if not path.exists("{}/{}".format(dst, a_file)):
                    logging.debug(
                        "{} not found in target env, adding from source env".format(
                            a_file
                        )
                    )
                    shutil.copy("{}/".format(curr_dir) + a_file, dst)
                    copied_files.append("{}/".format(dst) + a_file)
                    continue
                if a_file in tgtEnv.ENVIRONMENT_SPECIFIC_PARAMS.keys():
                    logging.debug(
                        "This file [{}] contains environment-specific parameters that need to be saved.".format(
                            a_file
                        )
                    )
                    # remember environment-specific information
                    store_environment_params(src, srcEnv, a_file)
                    env_params = store_environment_params(dst, tgtEnv, a_file)
                    logging.debug("Stored parameters: {}".format(env_params))
                    shutil.copy("{}/".format(curr_dir) + a_file, dst)

                    # re-apply all the stored environment-specific params
                    merge_json_file_with_stored_environment_params(
                        dst, a_file, env_params, srcEnv, tgtEnv
                    )
                if a_file in tgtEnv.PARAMS_TO_SET.keys():
                    logging.debug(
                        "Making sure this file [{}] has correct names.".format(a_file)
                    )
                    write_index_names(curr_dir, dst, a_file, tgtEnv)
                    # full_path_to_file = "{}/{}".format(dst, a_file)
                    # with open(full_path_to_file, 'r+') as f:
                    #     yaml = YAML(typ="safe")
                    #     yam_file = yaml.load(f)
                    #     create_env_index_name(tgtEnv, a_file, yam_file)
                    # target_mappings = tgtEnv.PARAMS_TO_SET[a_file]["mappings"]
                    # yam_mappings = yam_file["mappings"]
                    # for i in range(len(target_mappings)):
                    #     yam_mappings[i]["name"] = target_mappings[i]["name"]

                    # yaml=YAML()
                    # f.seek(0)
                    # yaml.default_flow_style = False
                    # yaml.dump(yam_file, f)
                    # f.truncate()
                else:
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
