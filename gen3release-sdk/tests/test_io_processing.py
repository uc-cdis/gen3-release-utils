import pytest
import json
import hashlib
import os
import copy
import time

from ruamel.yaml import YAML

from gen3release.config import env
from gen3release.filesys import io_processing as py_io
from tests.helpers import are_dir_trees_equal
from tests.conftest import setUp_tearDown, target_env, target_env

ABS_PATH = os.path.abspath(".")


@pytest.fixture()
def loaded_target_env():

    obj = env.Env(ABS_PATH + "/data/fake_target_env")
    obj.sower_jobs = [
        {
            "name": "pelican-export",
            "action": "export",
            "container": {
                "name": "job-task",
                "image": "quay.io/cdis/pelican-export:2020.06",
                "pull_policy": "Always",
                "env": [
                    {
                        "name": "DICTIONARY_URL",
                        "valueFrom": {
                            "configMapKeyRef": {
                                "name": "manifest-global",
                                "key": "dictionary_url",
                            }
                        },
                    },
                    {
                        "name": "GEN3_HOSTNAME",
                        "valueFrom": {
                            "configMapKeyRef": {
                                "name": "manifest-global",
                                "key": "hostname",
                            }
                        },
                    },
                    {"name": "ROOT_NODE", "value": "subject"},
                ],
                "volumeMounts": [
                    {
                        "name": "pelican-creds-volume",
                        "readOnly": True,
                        "mountPath": "/pelican-creds.json",
                        "subPath": "config.json",
                    },
                    {
                        "name": "peregrine-creds-volume",
                        "readOnly": True,
                        "mountPath": "/peregrine-creds.json",
                        "subPath": "creds.json",
                    },
                ],
                "cpu-limit": "1",
                "memory-limit": "12Gi",
            },
            "volumes": [
                {
                    "name": "pelican-creds-volume",
                    "secret": {"secretName": "pelicanservice-g3auto"},
                },
                {
                    "name": "peregrine-creds-volume",
                    "secret": {"secretName": "peregrine-creds"},
                },
            ],
            "restart_policy": "Never",
        },
        {
            "name": "ingest-metadata-manifest",
            "action": "ingest-metadata-manifest",
            "activeDeadlineSeconds": 86400,
            "serviceAccountName": "jobs-fake_target_env",
            "container": {
                "name": "job-task",
                "image": "quay.io/cdis/metadata-manifest-ingestion:2.1.6",
                "pull_policy": "Always",
                "env": [
                    {
                        "name": "GEN3_HOSTNAME",
                        "valueFrom": {
                            "configMapKeyRef": {
                                "name": "manifest-global",
                                "key": "hostname",
                            }
                        },
                    }
                ],
                "volumeMounts": [
                    {
                        "name": "creds-volume",
                        "readOnly": True,
                        "mountPath": "/creds.json",
                        "subPath": "creds.json",
                    }
                ],
                "cpu-limit": "1",
                "memory-limit": "1Gi",
            },
            "volumes": [
                {"name": "creds-volume", "secret": {"secretName": "sower-jobs-g3auto"}}
            ],
            "restart_policy": "Never",
        },
        {
            "name": "get-dbgap-metadata",
            "action": "get-dbgap-metadata",
            "serviceAccountName": "jobs-fake_target_env",
            "container": {
                "name": "job-task",
                "image": "quay.io/cdis/get-dbgap-metadata:1.1.6",
                "pull_policy": "Always",
                "env": [],
                "volumeMounts": [
                    {
                        "name": "creds-volume",
                        "readOnly": True,
                        "mountPath": "/creds.json",
                        "subPath": "creds.json",
                    }
                ],
                "cpu-limit": "1",
                "memory-limit": "1Gi",
            },
            "volumes": [
                {"name": "creds-volume", "secret": {"secretName": "sower-jobs-g3auto"}}
            ],
            "restart_policy": "Never",
        },
    ]
    obj.environment_specific_params = {
        "manifest.json": {
            "notes": [
                "This is a fake target environment manifest",
                "That's all I have to say",
            ],
            "global": {
                "environment": "stageprod",  # VPC
                "hostname": "fake_target_env",
                "revproxy_arn": "arn:aws:acm:us-east-1:895962626746:certificate/a82bb5ed-9ad1-444d-9bfd-5bc314541307",
                "kube_bucket": "kube-stageprod-gen3",
                "logs_bucket": "logs-stageprod-gen3",
                "sync_from_dbgap": "true",
                "useryaml_s3path": "s3://cdis-gen3-users/stageprod/user.yaml",
            },
            "scaling": {
                "arborist": {"strategy": "auto", "min": 2, "max": 4, "targetCpu": 40},
                "fence": {"strategy": "auto", "min": 5, "max": 15, "targetCpu": 40},
                "presigned-url-fence": {
                    "strategy": "auto",
                    "min": 2,
                    "max": 5,
                    "targetCpu": 40,
                },
                "indexd": {"strategy": "auto", "min": 2, "max": 4, "targetCpu": 40},
                "revproxy": {"strategy": "auto", "min": 2, "max": 4, "targetCpu": 40},
            },
        },
        "hatchery.json": {
            "user-namespace": "jupyter-pods-fake_target_env",
            "sidecar": {
                "env": {
                    "NAMESPACE": "fake_target_env",
                    "HOSTNAME": "fake_target_env.datastage.io",
                }
            },
        },
    }
    return obj


@pytest.fixture()
def manifestnaming_data():
    data = {
        "guppy": {
            "indices": [
                {"index": "fake_target_env_subject", "type": "subject"},
                {"index": "fake_target_env_file", "type": "file"},
            ],
            "config_index": "fake_target_env_array-config",
            "auth_filter_field": "auth_resource_path",
        }
    }
    return data


@pytest.fixture()
def etlMapping_data():
    data = None
    with open(ABS_PATH + "/data/fake_target_env/etlMapping.yaml") as f:
        yaml = YAML(typ="safe")
        data = yaml.load(f)
    return data


def test_generate_safe_index_name():
    """
    Test that created names are valid index names
    """
    ENV_IN = [
        # test bad chars
        r"s\ngen\"3.b/iodatac\\atalyst. |n:<>hlbi.nih\n.go\v\n",
        # test bad chars in start
        r"\\gen\3.bi\foda\btac\atalyst.nhlbinih.gov",
        # test bad start chars
        r"--gen3.\/[bi/odatacatalyst].nhlbi.nih.gov",
        # test bad start chars and capital letters
        r"+\agen3.BIOdatacatalyst.nhlbi.nih.gov",
        # test 255 byte limit
        r"this_is_number_____________________________________________________________________________________________________________________________________________________________________________________________________________________________0123456789101112",
    ]
    ENV_OUT = [
        r"s_ngen__3.b_iodatac__atalyst.__n___hlbi.nih_n.go_v_n_testtype",
        r"gen_3.bi_foda_btac_atalyst.nhlbinih.gov_testtype",
        r"gen3.__[bi_odatacatalyst].nhlbi.nih.gov_testtype",
        r"agen3.biodatacatalyst.nhlbi.nih.gov_testtype",
        r"this_is_number_____________________________________________________________________________________________________________________________________________________________________________________________________________________________01234567891_testtype",
    ]
    for (
        inp,
        oup,
    ) in zip(ENV_IN, ENV_OUT):
        print(f"input {inp}")
        output = py_io.generate_safe_index_name(inp, "testtype")
        print(f"output {output}")
        assert output == oup

    # Must have an environment name
    with pytest.raises(NameError):
        py_io.generate_safe_index_name("", "testtype")


def test_process_index_names(target_env, manifestnaming_data, etlMapping_data):
    """
    Test that created names are correctly assigned to fields
    """
    # test names in manifest
    param_guppy = target_env.params_to_set["manifest.json"].get("guppy")
    file_guppy = manifestnaming_data.get("guppy")
    py_io.process_index_names(
        target_env.name, param_guppy, file_guppy, "indices", "type", "index"
    )
    expected_guppy = {
        "indices": [
            {"index": "fake_target_env_subject", "type": "subject"},
            {"index": "fake_target_env_file", "type": "file"},
        ],
        "config_index": "fake_target_env_array-config",
        "auth_filter_field": "auth_resource_path",
    }
    assert file_guppy == expected_guppy

    # test names in etlMapping
    py_io.process_index_names(
        target_env.name,
        target_env.params_to_set["etlMapping.yaml"],
        etlMapping_data,
        "mappings",
        "doc_type",
        "name",
    )
    expected_yaml_names = ["fake_target_env_subject", "fake_target_env_file"]
    names = [d["name"] for d in etlMapping_data.get("mappings")]
    assert expected_yaml_names == names


def test_create_env_index_name(target_env, manifestnaming_data, etlMapping_data):
    """
    Test that created names have the form <commonsname_type>
    """
    py_io.create_env_index_name(target_env, "manifest.json", manifestnaming_data)
    guppy = manifestnaming_data.get("guppy")
    expected_guppy = {
        "indices": [
            {"index": "fake_target_env_subject", "type": "subject"},
            {"index": "fake_target_env_file", "type": "file"},
        ],
        "config_index": "fake_target_env_array-config",
        "auth_filter_field": "auth_resource_path",
    }
    assert guppy == expected_guppy

    py_io.create_env_index_name(target_env, "etlMapping.yaml", etlMapping_data)
    expected_yaml_names = ["fake_target_env_subject", "fake_target_env_file"]
    names = [d["name"] for d in etlMapping_data.get("mappings")]
    assert expected_yaml_names == names


def test_store_environment_params(target_env, loaded_target_env):
    """
    Test that environment params are loaded into environment object
    """

    # test loading of manifest env params
    with open(ABS_PATH + "/data/fake_target_env/manifest.json", "r") as f:
        mdata = json.loads(f.read())

    py_io.store_environment_params(mdata, target_env, "manifest.json")
    sowers = target_env.sower_jobs
    expected_sower = loaded_target_env.sower_jobs
    assert expected_sower == sowers
    env_params = target_env.environment_specific_params
    expected_params = loaded_target_env.environment_specific_params
    assert (
        expected_params["manifest.json"] == env_params["manifest.json"]
    ), f"Got: {env_params}"

    # Test loading of hatchery env params
    with open(
        ABS_PATH + "/data/fake_target_env/manifests/hatchery/hatchery.json", "r"
    ) as f:
        hdata = json.loads(f.read())

    py_io.store_environment_params(
        hdata,
        target_env,
        "hatchery.json",
    )
    assert expected_params["hatchery.json"] == env_params["hatchery.json"]


def test_merge():
    """
    Test that source (saved target environment params) dictionary is merged into target dictionary
    """
    src_dict_example = {
        "scaling": {
            "arborist": {"strategy": "fast", "min": 0, "max": 0, "targetCpu": 0},
            "fence": {"min": 0, "max": 0, "targetCpu": 0},
            "presigned-url-fence": {"strategy": "slow", "max": 15, "targetCpu": 4},
        },
        "S3_BUCKETS": {
            "COPY_ALL": {
                "cdis-presigned-url-test-target": {
                    "role-arn": "arn:aws:iam::707767160287:role/bucket_reader_writer_to_cdistest-presigned-url_role",
                    "cred": "target",
                }
            }
        },
    }
    tgt_dict_example = {
        "global": {
            "environment": "testenv",
            "hostname": "testenv.net",
        },
        "scaling": {
            "arborist": {"strategy": "fast", "min": 0, "max": 0, "targetCpu": 0},
            "fence": {"strategy": "auto", "min": 5, "max": 15, "targetCpu": 4},
            "presigned-url-fence": {
                "strategy": "slow",
                "min": 2,
                "max": 5,
                "targetCpu": 40,
            },
        },
        "S3_BUCKETS": {
            "This should not exist": {
                "role-arn": "Not to be in output",
            }
        },
    }

    tgt_merged = py_io.merge(src_dict_example, tgt_dict_example)
    expected_dict = {
        "global": {
            "environment": "testenv",
            "hostname": "testenv.net",
        },
        "scaling": {
            "arborist": {"strategy": "fast", "min": 0, "max": 0, "targetCpu": 0},
            "fence": {"strategy": "auto", "min": 0, "max": 0, "targetCpu": 0},
            "presigned-url-fence": {
                "strategy": "slow",
                "min": 2,
                "max": 15,
                "targetCpu": 4,
            },
        },
        "S3_BUCKETS": {
            "cdis-presigned-url-test-target": {
                "role-arn": "arn:aws:iam::707767160287:role/bucket_reader_writer_to_cdistest-presigned-url_role",
                "cred": "target",
            }
        },
    }

    assert expected_dict == tgt_merged


def test_process_sower_jobs():
    """
    Test that sower jobs in target are updated but jobs are not already found in target
    are not included
    """
    source_sower = [
        {
            "name": "fakejob1",
            "container": {
                "image": "quay.io/cdis/fancyimage",
                "pull_policy": "Never",
                "env": [
                    {
                        "name": "DICTIONARY_URL",
                        "valueFrom": {
                            "configMapKeyRef": {
                                "name": "manifest-local",
                                "key": "dictionary_url",
                            }
                        },
                    }
                ],
            },
        },
        {
            "name": "fakejob2",
            "serviceAccountName": "jobs-fake_source_env",
            "container": {
                "image": "quay.io/cdis/fancy",
                "pull_policy": "Never",
                "env": [
                    {
                        "name": "GEN3_HOSTNAME",
                        "valueFrom": {
                            "configMapKeyRef": {
                                "name": "manifest-local",
                                "key": "hostname",
                            }
                        },
                    }
                ],
            },
        },
    ]
    target_sower = [
        {
            "name": "fakejob2",
            "serviceAccountName": "jobs-fake_target_env",
            "container": {
                "image": "quay.io/cdis/NOTfancy",
                "pull_policy": "Always",
                "env": [
                    {
                        "name": "GEN3_HOSTNAME",
                        "valueFrom": {
                            "configMapKeyRef": {
                                "name": "manifest-global",
                                "key": "hostname",
                            }
                        },
                    }
                ],
            },
        }
    ]

    data = py_io.process_sower_jobs({}, source_sower, target_sower)
    assert data["sower"] == [
        {
            "name": "fakejob2",
            "serviceAccountName": "jobs-fake_target_env",
            "container": {
                "image": "quay.io/cdis/fancy",
                "pull_policy": "Never",
                "env": [
                    {
                        "name": "GEN3_HOSTNAME",
                        "valueFrom": {
                            "configMapKeyRef": {
                                "name": "manifest-local",
                                "key": "hostname",
                            }
                        },
                    }
                ],
            },
        }
    ]

    # Don't write sowers if none exist
    target_sower = []
    data = py_io.process_sower_jobs({}, source_sower, target_sower)
    assert not data.get("sower")


def test_clean_dictionary():
    """
    Test that keys with null values are removed
    """
    nestedempty = {
        "scaling": {
            "arborist": {"strategy": "", "min": "", "max": "", "targetCpu": ""},
            "fence": {"strategy": "auto", "min": 32, "max": 10, "targetCpu": 10},
            "presigned-url-fence": {},
        }
    }
    expected = {
        "scaling": {
            "fence": {"strategy": "auto", "min": 32, "max": 10, "targetCpu": 10},
        }
    }
    outdict = py_io.clean_dictionary(nestedempty)

    assert outdict == expected


def test_recursive_copy(source_env, setUp_tearDown):
    """
    Test that all files and subfolders are copied from source env to target env
    """
    temp_tgt = env.Env(f"{ABS_PATH}/data/temp_target_env")
    files = py_io.recursive_copy(
        target_env, temp_tgt, source_env.full_path, temp_tgt.full_path
    )

    os.chdir(ABS_PATH)
    assert len(files) == 10
    assert are_dir_trees_equal(
        ABS_PATH + "/data/temp_target_env", ABS_PATH + "/data/fake_source_env"
    )


def test_write_out_file(setUp_tearDown):
    path = f"{ABS_PATH}/data/temp_target_env/tempfile.txt"
    data = {"data": "fakedata"}
    # catch improper flags
    with pytest.raises(AssertionError):
        py_io.write_out_file(path, data, "r")


def test_read_in_file():
    path = f"{ABS_PATH}/data/test_references/testmerge_manifest.json"
    # catch imporper flags
    with pytest.raises(AssertionError):
        py_io.read_in_file(path, "r+")

    # must be yaml or json
    with pytest.raises(NameError):
        py_io.read_in_file(f"{ABS_PATH}/__init__.py", "r")
