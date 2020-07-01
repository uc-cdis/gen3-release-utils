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
  with open(manifest, 'r') as m:
    contents = m.read()
    return hashlib.md5(contents.encode('utf-8')), json.loads(contents)

def merge(source, destination):
  "Recursively merges dictionary source into dictionary destination"""
  for key, value in source.items():
      if isinstance(value, dict):
          # get node or create one
          node = destination.setdefault(key, {})
          merge(value, node)
      else:
          destination[key] = value

  return destination

def write_into_manifest(manifest, json_with_changes):
  with open(manifest, 'r+') as m:
    m.seek(0)
    m.write(json.dumps(json_with_changes, indent=2))
    m.truncate()
    return hashlib.md5(m.read().encode('utf-8'))

def merge_json_file_with_stored_environment_params(dst_path, the_file, env_params, srcEnc, trgEnv):
  full_path_to_file = '{}/{}'.format(dst_path, the_file)
  logging.debug('merging stored data from [{}] into {}'.format(the_file, full_path_to_file))
  if the_file == 'etlMapping.yaml':
    with open(full_path_to_file, 'r') as f:

      yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
      json_file = yaml.load(f)
      items = json_file['mappings']
      for i in range(len(items)):
        items[i]['name'] = env_params['mappings'][i]['name']

    ###For coverting to json
      # merged_json = {**json_file, **env_params}
    # path = full_path_to_file.replace("yaml", "json")

    # with open(path, 'w') as f:
    #   f.write(json.dumps(json_file, indent=2))
    # os.system("rm {}".format(full_path_to_file))
    with open(full_path_to_file, 'w') as f:
      yaml=YAML()
      yaml.default_flow_style = False
      yaml.dump(json_file, f)

  else:
    with open(full_path_to_file, 'r+') as f:
      json_file = json.loads(f.read())
      # merged_json = {**json_file, **env_params}
      # merged_json = {**env_params, **json_file}
      merged_json = merge(env_params, json_file)
      if the_file == "manifest.json":
        merged_json = remove_superfluous_from_sowers(merged_json, srcEnc, trgEnv)
        merged_json = handle_guppy(merged_json, srcEnc, trgEnv)
      f.seek(0)
      f.write(json.dumps(merged_json, indent=2))
      f.truncate()

def handle_guppy(mani_json, srcEnv, trgEnv):
  gp = mani_json.get("guppy")
  if not gp:
    return mani_json
  indices = gp['indices']
  for i in indices:
    i["index"] = trgEnv.name + "_" + i['type']
  gp['config_index'] = trgEnv.name + "_" + "array-config"
  return mani_json


def remove_superfluous_from_sowers(mani_json, srcEnv, trgEnv):
  superflous_resources = []
  if len(srcEnv.SOWER) == len(trgEnv.SOWER):
    return mani_json

  srcnames = [x["name"] for x in srcEnv.SOWER]
  trgnames = [x["name"] for x in trgEnv.SOWER]
  for name in srcnames:
    if name not in trgnames:
      superflous_resources.append(name)
  logging.debug("Original Target environment does not have {}, removing from target".format(superflous_resources))

  mani_json["sower"] = [x for x in mani_json["sower"] if x["name"] not in superflous_resources]
  return mani_json

def recursive_copy(copied_files, srcEnv, tgtEnv, src, dst):
  os.chdir(src)
  curr_dir = os.getcwd()
  logging.debug('current_dir: {}'.format(curr_dir))
  try:
    for a_file in os.listdir():
      if a_file == 'README.md': continue
      logging.debug('copying file: {}'.format(('{}/'.format(curr_dir) + a_file)))
      if os.path.isdir('{}/'.format(os.getcwd()) + a_file):
        logging.debug('this file {} is a directory. Stepping into it'.format(a_file))
        new_dst = os.path.join(dst, a_file)
        os.makedirs(new_dst, exist_ok=True)
        curr_src = os.path.abspath(a_file)
        recursive_copy(copied_files, srcEnv, tgtEnv, curr_src, new_dst)
        logging.debug('finished recursion on folder: {}'.format(a_file))
        os.chdir(os.path.abspath('..'))
      else:
        logging.debug('copying {} into {}'.format(a_file, dst))
        # TODO: Due to etlMapping.yaml, we need a YAMl parsing module
        # files mapped in ENVIRONMENT_SPECIFIC_PARAMS need special treatment
        if path.exists("{}/{}".format(dst, a_file)):
          if a_file == 'manifest.json': 
            logging.debug("Loading source and dest sowers into env")
            with open('{}/{}'.format(src, a_file), 'r') as j:
              json_file = json.loads(j.read())
              try:
                srcEnv.SOWER = json_file["sower"]
              except KeyError:
                srcEnv.SOWER = []
            with open('{}/{}'.format(dst, a_file), 'r') as j:
              json_file = json.loads(j.read())
              try:
                tgtEnv.SOWER = json_file["sower"]
              except KeyError:
                tgtEnv.SOWER = []
                    

          if a_file in tgtEnv.ENVIRONMENT_SPECIFIC_PARAMS.keys():
            logging.debug('This file [{}] contains environment-specific parameters that need to be saved.'.format(a_file))
            # remember environment-specific information
            json_file = None
            if '.yaml' in a_file:
              with open('{}/{}'.format(dst, a_file), 'r') as j:

                yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
                json_file = yaml.load(j)

            else:
              with open('{}/{}'.format(dst, a_file), 'r') as j:
                json_file = json.loads(j.read())
            env_params = tgtEnv.load_environment_params(a_file, json_file)
            logging.debug('Stored parameters: {}'.format(env_params))

            shutil.copy('{}/'.format(curr_dir) + a_file, dst)
            # re-apply all the stored environment-specific params
            merge_json_file_with_stored_environment_params(dst, a_file, env_params, srcEnv, tgtEnv)
          

        else:
          shutil.copy('{}/'.format(curr_dir) + a_file, dst)
        copied_files.append('{}/'.format(dst) + a_file)
    return copied_files
  except Exception as e:
    logging.error('something went wrong during the recursive copy of [{}] into [{}]'.format(srcEnv.name, tgtEnv.name))
    traceback.print_exc()
