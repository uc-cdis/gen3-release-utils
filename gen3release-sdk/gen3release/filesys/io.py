import hashlib
import shutil
from ..config.env import Env
from shutil import copytree, Error
import logging
import json
import os
import traceback

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger(__name__)

def read_manifest(manifest):
  with open(manifest, 'r') as m:
    contents = m.read()
    return hashlib.md5(contents.encode('utf-8')), json.loads(contents)

def write_into_manifest(manifest, json_with_changes):
  with open(manifest, 'r+') as m:
    m.seek(0)
    m.write(json.dumps(json_with_changes, indent=2))
    m.truncate()
    return hashlib.md5(m.read().encode('utf-8'))

def merge_json_file_with_stored_environment_params(dst_path, the_file, env_params):
  full_path_to_file = '{}/{}'.format(dst_path, the_file)
  logging.debug('merging stored data from [{}] into {}'.format(the_file, full_path_to_file))
  with open(full_path_to_file, 'r+') as f:
    json_file = json.loads(f.read())
    merged_json = {**json_file, **env_params}
    f.seek(0)
    f.write(json.dumps(merged_json, indent=2))
    f.truncate()


def recursive_copy(copied_files, srcEnv, tgtEnv, src, dst):
  os.chdir(src)
  try:
    for a_file in os.listdir():
      if a_file == 'README.md': continue
      logging.debug('copying file: {}'.format(a_file))
      if os.path.isdir(a_file):
        new_dst = os.path.join(dst, a_file)
        os.makedirs(new_dst, exist_ok=True)
        recursive_copy(copied_files, srcEnv, tgtEnv, os.path.abspath(a_file) + '/', new_dst)
      else:
        logging.debug('copying {} into {}'.format(a_file, dst))
        # files mapped in ENVIRONMENT_SPECIFIC_PARAMS need special treatment
        if a_file in tgtEnv.ENVIRONMENT_SPECIFIC_PARAMS.keys():
          logging.debug('This file [{}] contains environment-specific \
parameters that need to be saved.'.format(a_file))
          # remember environment-specific information
          json_file = None
          with open('{}/{}'.format(dst, a_file), 'r') as j:
            json_file = json.loads(j.read())
          env_params = tgtEnv.load_environment_params(a_file, json_file)
          shutil.copy('{}/'.format(src) + a_file, dst)
          logging.debug('Stored parameters: {}'.format(env_params))
          # re-apply all the stored environment-specific params
          merge_json_file_with_stored_environment_params(dst, a_file, env_params)
        else:
          shutil.copy(src + a_file, dst)
        copied_files.append('{}/'.format(dst) + a_file)
    logging.debug('copied files: {}'.format(copied_files))
    return copied_files
  except Exception as e:
    logging.error('something went wrong during the recursive copy of [{}] into [{}]'.format(srcEnv.name, tgtEnv.name))
    traceback.print_exc()
