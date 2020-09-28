import hashlib
import shutil
from shutil import copytree, Error
import logging
import json
import os
import traceback
from os import path
import re
from collections import defaultdict

from ruamel.yaml import YAML

from config.env import Env


LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger(__name__)


def generate_safe_index_name(envname, doctype):
    """Makes sure index name follow rules set in
    https://www.elastic.co/guide/en/elasticsearch/reference/7.5/indices-create-index.html#indices-create-api-path-params"""
    if not doctype:
        raise NameError("No type given. Environment needs a type")

    BAD_CHARS = '[\\\\/*?"<>| ,#:]'
    envname = re.sub(BAD_CHARS, "_", envname)

    BAD_START_CHARS = "-_+"
    doctype = re.sub(BAD_CHARS, "_", doctype)
    MAX_LEN = 255 - (len("_") + len(doctype.encode("utf8")))

    env_name = envname.lstrip(BAD_START_CHARS)
    if not env_name:
        raise NameError("Environment needs a name with valid characters")

    env_name = env_name.encode("utf8")[:MAX_LEN].decode("utf8")
    outname = env_name + "_" + doctype
    return outname.lower()


def process_index_names(envname, block, file_data, key, typ, subkey):
    "Assigns index names in the file in the form of <commonsname>_<type>"
    types_seen = defaultdict(int)
    for index in file_data.get(key, []):
        inx_type = index.get(typ)
        if not inx_type:
            raise KeyError(
                "No type found in {}, in {} a type must be given".format(index, envname)
            )
        typename = inx_type + (
            str(types_seen[inx_type]) if types_seen[inx_type] else ""
        )
        types_seen[inx_type] += 1
        index_name = generate_safe_index_name(envname, typename)
        logging.debug("Adding index name: {} ".format(index_name))
        block[key].append({subkey: index_name})

    for i in range(len(file_data[key])):
        file_data[key][i][subkey] = block[key][i][subkey]


def create_env_index_name(tgtenv_obj, the_file, srcdata):

    params = tgtenv_obj.params_to_set[the_file]
    if the_file == "manifest.json":
        param_guppy = params["guppy"]
        file_guppy = srcdata.get("guppy")
        if not file_guppy:
            return
        key = "indices"
        typ = "type"
        subkey = "index"
        process_index_names(tgtenv_obj.name, param_guppy, file_guppy, key, typ, subkey)

        config_index = file_guppy.get("config_index")
        if config_index:
            param_guppy["config_index"] = tgtenv_obj.name + "_" + "array-config"
        if param_guppy.get("config_index"):
            file_guppy["config_index"] = param_guppy["config_index"]

    elif the_file == "etlMapping.yaml":
        key = "mappings"
        typ = "doc_type"
        subkey = "name"
        process_index_names(
            tgtenv_obj.name,
            tgtenv_obj.params_to_set[the_file],
            srcdata,
            key,
            typ,
            subkey,
        )


def read_in_file(filepath, flag):
    assert flag in ["r", "rb"], "must be a read only flag"
    with open(filepath, flag) as fd:
        data = None
        if filepath.endswith(".yaml") or filepath.endswith("yml"):
            yaml = YAML()
            yaml.preserve_quotes = True
            data = yaml.load(fd)
        elif filepath.endswith(".json"):
            data = json.loads(fd.read())
    if not data:
        raise NameError(f"Failed to read in {filepath}, file must be yaml or json")
    return data


def write_out_file(filepath, data, flag):
    assert flag in ["w", "w+", "wb"], "must be a write flag"
    with open(filepath, flag) as fd:
        if filepath.endswith(".yaml") or filepath.endswith("yml"):
            yaml = YAML()
            yaml.default_flow_style = False
            yaml.indent(offset=2, sequence=4, mapping=2)
            yaml.dump(data, fd)
        elif filepath.endswith(".json"):
            fd.write(json.dumps(data, indent=2))
            fd.write("\n")
    logging.debug("Wrote file {}".format(filepath))


def store_environment_params(data, env_obj, filename):

    if filename == "manifest.json":
        env_obj.load_sower_jobs(data)
    return env_obj.load_environment_params(filename, data)


def read_manifest(manifest):
    with open(manifest, "r") as m:
        contents = m.read()
        return hashlib.md5(contents.encode("utf-8")), json.loads(contents)


def merge(source, destination):
    "Recursively merges dictionary source into dictionary destination"
    for key, value in source.items():
        if isinstance(value, dict) and value.get("COPY_ALL"):
            destination[key] = value.get("COPY_ALL")
        elif isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            if value or value == 0:
                destination[key] = value
            else:
                destination.pop(key, None)

    return destination


def write_into_manifest(manifest, json_with_changes):
    with open(manifest, "r+") as m:
        m.seek(0)
        m.write(json.dumps(json_with_changes, indent=2))
        m.truncate()
        return hashlib.md5(m.read().encode("utf-8"))


def process_sower_jobs(mani_json, srcEnv_sowers, tgtEnv_sowers):
    """
    Deletes sower jobs added to target environment if wasn't already in
    target environment. Retains target's service account name.
    """
    superflous_resources = []
    if not tgtEnv_sowers:
        mani_json.pop("sower", None)
        return mani_json
    elif not srcEnv_sowers:
        return mani_json

    srcnames = [x.get("name") for x in srcEnv_sowers]
    tgtnames = [x.get("name") for x in tgtEnv_sowers]
    for name in srcnames:
        if name not in tgtnames:
            superflous_resources.append(name)
    logging.debug(
        "Original target environment does not have {}, removing from target".format(
            superflous_resources
        )
    )
    mani_json["sower"] = [
        x for x in srcEnv_sowers if x["name"] not in superflous_resources
    ]

    for t_job, s_job in zip(tgtEnv_sowers, mani_json["sower"]):
        accountname = t_job.get("serviceAccountName")
        if accountname:
            s_job["serviceAccountName"] = accountname
    return mani_json


def clean_dictionary(dic):
    """
    Removes all keys in a nested dictionary that have null values
    """
    if not isinstance(dic, (dict, list)):
        return dic
    if isinstance(dic, list):
        return [v for v in (clean_dictionary(v) for v in dic) if v or v == 0]
    return {
        k: v
        for k, v in ((k, clean_dictionary(v)) for k, v in dic.items())
        if v and v != -1
    }


def recursive_copy(srcEnv, tgtEnv, src, dst):
    files_copied = {}

    def recurse(srcEnv, tgtEnv, src, dst):
        os.chdir(src)
        curr_dir = os.getcwd()
        logging.debug("current_dir: {}".format(curr_dir))
        for a_file in os.listdir():
            if a_file == "README.md":
                continue
            logging.debug("copying file: {}".format(("{}/".format(curr_dir) + a_file)))
            if os.path.isdir("{}/".format(os.getcwd()) + a_file):
                logging.debug(
                    "this file {} is a directory. Stepping into it".format(a_file)
                )
                a_folder = a_file
                new_dst = os.path.join(dst, a_folder)
                os.makedirs(new_dst, exist_ok=True)
                curr_src = os.path.abspath(a_folder)
                recurse(srcEnv, tgtEnv, curr_src, new_dst)
                logging.debug("finished recursion on folder: {}".format(a_folder))
                os.chdir(os.path.abspath(".."))
            else:
                logging.debug("copying {} into {}".format(a_file, dst))
                src_filepath = "{}/".format(curr_dir) + a_file
                tgt_filepath = "{}/".format(dst) + a_file
                files_copied[src_filepath] = False
                modified_file = False
                if not path.exists("{}/{}".format(dst, a_file)):
                    logging.debug(
                        "File [{}] not found in target env, adding from source env".format(
                            src + "/" + a_file
                        )
                    )
                    shutil.copy("{}/".format(curr_dir) + a_file, dst)
                    files_copied[src_filepath] = True
                    continue

                # files mapped in environment_specific_params need special treatment
                params_template = tgtEnv.environment_specific_params.get(a_file)
                names_template = tgtEnv.params_to_set.get(a_file)
                if params_template or names_template:
                    src_data = read_in_file(src_filepath, "r")
                    tgt_data = read_in_file(tgt_filepath, "r")

                    if params_template:
                        logging.debug(
                            "This file [{}] contains environment-specific parameters that need to be saved.".format(
                                dst + "/" + a_file
                            )
                        )
                        if a_file == "manifest.json":
                            srcEnv.load_sower_jobs(src_data)
                            tgtEnv.load_sower_jobs(tgt_data)

                        tgt_envparams = tgtEnv.load_environment_params(a_file, tgt_data)

                        logging.debug(
                            "Stored target parameters: {}".format(tgt_envparams)
                        )

                        if a_file == "manifest.json":
                            src_data = process_sower_jobs(
                                src_data, srcEnv.sower_jobs, tgtEnv.sower_jobs
                            )

                        src_data = merge(
                            tgtEnv.environment_specific_params[a_file], src_data
                        )
                        # Remove any fields with no data
                        src_data = clean_dictionary(src_data)

                        # Assure no keys without values
                        modified_file = True

                    if names_template:
                        logging.debug(
                            "Making sure this file [{}] has correct names.".format(
                                a_file
                            )
                        )
                        create_env_index_name(tgtEnv, a_file, src_data)
                        modified_file = True

                    if modified_file:
                        write_out_file(tgt_filepath, src_data, "w")
                        files_copied[src_filepath] = True
                else:
                    assert not files_copied.get(
                        src_filepath
                    ), "Attempting to copy file that's already copied"
                    shutil.copy(src_filepath, tgt_filepath)
                    files_copied[src_filepath] = True

        return files_copied

    try:
        return recurse(srcEnv, tgtEnv, src, dst)
    except Exception as e:
        logging.error(
            "something went wrong during the recursive copy of [{}] into [{}]".format(
                srcEnv.name, tgtEnv.name
            )
        )
        traceback.print_exc(e)
        return {}
