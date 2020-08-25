import pytest
import json
import os

from gen3release.config import env
from tests.conftest import target_env


def test___init___():
    """
    Test that the constructor correctly assigns member variables
    """
    envobj = env.Env("./data/fake_target_env")
    assert envobj.name == "fake_target_env"
    assert envobj.repo_dir == "data"
    assert envobj.full_path == os.path.abspath("./data/fake_target_env")


def test_load_environment_params(target_env):
    """
    Test that environment specifc params are correctly loaded into ENVIRONMENT_SPECIFIC PARMS
    """
    json_data = {
        "notes": ["These values should be loaded into env"],
        "global": {
            "environment": "A test env",  # VPC
            "hostname": "",
            "revproxy_arn": "",
            "kube_bucket": "kub buck",
            "logs_bucket": "some bucket",
            "sync_from_dbgap": "",
            "useryaml_s3path": "",
        },
        "hatchery": {
            "user-namespace": "a namespace",
            "sidecar": {
                "env": {"NAMESPACE": "blank", "HOSTNAME": "not blank"}
            },  # KUBE_NAMESPACE
        },
    }
    env_params = target_env.environment_specific_params
    target_env.load_environment_params("manifest.json", json_data)
    assert json_data.get("notes") == env_params["manifest.json"].get("notes")
    assert json_data.get("global") == env_params["manifest.json"].get("global")
    assert json_data.get("hatchery") == env_params["manifest.json"].get("hatchery")
    assert not env_params["manifest.json"].get("scaling")

    # Test load nonresursed dict params
    yaml_data = {
        "S3_BUCKETS": {
            "cdis-presigned-url-test-target": {
                "role-arn": "arn:aws:iam::707767160287:role/bucket_reader_writer_to_cdistest-presigned-url_role",
                "cred": "target",
            },
            "faketarget-data-bucket": {
                "role-arn": "arn:aws:iam::707767160287:role/bucket_reader_writer_to_qaplanetv1-data-bucket_role",
                "cred": "target",
            },
        },
    }
    target_env.load_environment_params("fence-config-public.yaml", yaml_data)
    assert yaml_data.get("BASE_URL") == env_params["fence-config-public.yaml"].get(
        "BASE_URL"
    )
    assert {"COPY_ALL": yaml_data.get("S3_BUCKETS")} == env_params[
        "fence-config-public.yaml"
    ].get("S3_BUCKETS")
    assert yaml_data.get("LOGIN_REDIRECT_WHITELIST") == env_params[
        "fence-config-public.yaml"
    ].get("LOGIN_REDIRECT_WHITELIST")


def test_load_sower_jobs(target_env):
    """
    Test that sower jobs are correctly loaded into sower_jobs member variable
    """
    json_data = {
        "sower": [
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
            }
        ]
    }
    target_env.load_sower_jobs(json_data)
    sowersgot = json_data.get("sower_jobs")
    assert target_env.sower_jobs == json_data.get("sower")


def test_save_blocks(target_env):
    data = {
        "scaling": {
            "arborist": {"strategy": "strat1", "min": 10, "max": 10, "targetCpu": 10},
            "fence": {"strategy": "strat2", "min": 10, "max": 10, "targetCpu": 10},
            "presigned-url-fence": {
                "strategy": "",
                "min": 10,
                "max": 10,
                "targetCpu": 10,
            },
            "indexd": {"strategy": "1", "min": 10, "max": 10, "targetCpu": 110},
            "revproxy": {"strategy": "1", "min": 10, "max": 10, "targetCpu": 10},
        },
    }

    mockenv_params = target_env.environment_specific_params["manifest.json"]

    target_env.save_blocks("scaling", mockenv_params, data)
    assert mockenv_params["scaling"] == data["scaling"]


def test_find_and_replace(target_env):
    """
    Tests that versions are updated and ignored versions are not
    """
    manifest_data = {
        "versions": {
            "arborist": "quay.io/cdis/arborist:2020.07",
            "aws-es-proxy": "abutaha/aws-es-proxy:0.8",
            "ambassador": "quay.io/datawire/ambassador:1.4.2",
        },
        "sower": [
            {
                "name": "fakejob1",
                "container": {"image": "quay.io/cdis/fakejob1:2020.06"},
            },
            {
                "name": "fakejob2",
                "container": {"image": "quay.io/cdis/fakejob2:2020.06"},
            },
        ],
        "jupyterhub": {"sidecar": "quay.io/cdis/gen3fuse-sidecar:2020.08"},
        "ssjdispatcher": {
            "job_images": {"indexing": "quay.io/cdis/indexs3client:2020.07"}
        },
    }

    # Test manifest.json
    target_env.find_and_replace(
        "2020.20",
        '{"ambassador":"quay.io/datawire/ambassador:9000"}',
        "manifest.json",
        manifest_data,
    )
    expected_manifest = {
        "versions": {
            "arborist": "quay.io/cdis/arborist:2020.20",
            "aws-es-proxy": "abutaha/aws-es-proxy:0.8",
            "ambassador": "quay.io/datawire/ambassador:9000",
        },
        "sower": [
            {
                "name": "fakejob1",
                "container": {"image": "quay.io/cdis/fakejob1:2020.20"},
            },
            {
                "name": "fakejob2",
                "container": {"image": "quay.io/cdis/fakejob2:2020.20"},
            },
        ],
        "jupyterhub": {"sidecar": "quay.io/cdis/gen3fuse-sidecar:2020.20"},
        "ssjdispatcher": {
            "job_images": {"indexing": "quay.io/cdis/indexs3client:2020.20"}
        },
    }

    assert manifest_data == expected_manifest

    # Test hatchery.json
    hatch = {"sidecar": {"image": "quay.io/cdis/gen3fuse-sidecar:0.1.5"}}

    target_env.find_and_replace(
        "2020.20",
        '{"ambassador":"quay.io/datawire/ambassador:9000"}',
        "manifests/hatchery/hatchery.json",
        hatch,
    )

    assert hatch == {"sidecar": {"image": "quay.io/cdis/gen3fuse-sidecar:2020.20"}}
