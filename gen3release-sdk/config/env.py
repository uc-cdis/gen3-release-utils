import re
import os
import logging

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger(__name__)

class Env():
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

  def __init__(self, path_to_env_folder):
    """
     Creates an EnvironmentConfig object to store information related to its folder path and the name of the environment.
     This class also contains helper methods to facilitate the manipulation of config data.
    """
    environment_path_regex = re.search(r'(.*)\/(.*)', path_to_env_folder)
    logging.debug('identifying repo directory and name of the environment: {}'.format(str(environment_path_regex)))
    self.repo_dir = environment_path_regex.group(1)
    self.name = environment_path_regex.group(2)

  def _replace_all_versions(self, version, json_block):
    for svc in json_block:
      if svc not in self.SVCS_TO_IGNORE:
        logging.debug('applying version {} to {}'.format(version, svc))
        json_block[svc] = '{}:{}'.format(json_block[svc].split(':')[0], version)
    return json_block

  def _replace_on_path(self, version, json_block, path):
    if type(path) is list:
      # Hardcode index 0 for now as we only have a single sower job in the config
      # TODO: Iterate through indices of sower jobs blocks and replace versions accordingly
      self._replace_on_path(version, json_block[0], path[0])
    else:
      for sub_block, img_ref in path.items():
        logging.debug('replacing {} in {}'.format(img_ref, sub_block))
        json_block[sub_block][img_ref] = '{}:{}'.format(json_block[sub_block][img_ref].split(':')[0], version)
    return json_block

  def find_and_replace(self, version, manifest_file_name, json):
    for block in list(self.BLOCKS_TO_UPDATE[manifest_file_name].keys()):
      logging.debug('block: {}'.format(block))
      if block == 'versions':
        logging.debug('updating versions block from {}'.format(manifest_file_name))
        json[block] = self._replace_all_versions(version, json[block])
      else:
        logging.debug('updating {} block from {}'.format(block, '{}.json'.format(manifest_file_name)))
        json_block = json[block] if block != 'root' else json
        json_block = self._replace_on_path(version, json_block, self.BLOCKS_TO_UPDATE[manifest_file_name][block])

    return json

  def merge_json_file_with_stored_environment_params(self, dst_path, the_file, env_params):
    full_path_to_file = '{}/{}'.format(dst_path, the_file)
    logging.debug('merging stored data from [{}] into {}'.format(the_file, full_path_to_file))
    with open(full_path_to_file, 'r+') as f:
      json_file = json.loads(f.read())
      merged_json = {**json_file, **env_params}
      f.seek(0)
      f.write(json.dumps(merged_json, indent=2))
      f.truncate()
   
  def save_blocks(self, block, env_params, json_block):
    print('block: {}'.format(block))
    if type(env_params[block]) is dict:
      for sub_block in env_params[block].keys():
        # if the value of a given key is a dict and it is declared in ENVIRONMENT_SPECIFIC_PARAMS
        # apply recursion to store these parameters
        save_blocks(sub_block, env_params[block], json_block[block])
    else:
      logging.debug('saving block [{}]. Here is the value from the file: {}'.format(block, json_block[block]))
      env_params[block] = json_block[block]
   
  def load_environment_params(self, dst_path, the_file):
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


