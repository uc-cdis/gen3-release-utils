import pytest
import json
import os
import argparse
from argparse import Namespace
from unittest.mock import Mock, patch, call

from github.Repository import Repository

from gen3release import env_cli
from gen3release.config.env import Env
from tests.helpers import are_dir_trees_equal
from tests.conftest import setUp_tearDown

ABS_PATH = os.path.abspath(".")


def test_make_parser():
    """
    Test that arguments are parsed into correct variables
    """
    parser = env_cli.make_parser()
    args = parser.parse_args(
        [
            "copy",
            "-s",
            "/home/usr/demo/environment1",
            "-e",
            "/home/usr/demo/environment2",
        ]
    )
    assert args.env == "/home/usr/demo/environment2"
    assert args.func == env_cli.copy
    parser2 = env_cli.make_parser()
    args = parser2.parse_args(
        ["apply", "-v", "/home/usr/demo/environment1", "-e", "/home/usr/demo/targetenv"]
    )
    assert args.env == "/home/usr/demo/targetenv"
    assert args.func == env_cli.apply


@patch("gen3release.env_cli.Gh")
@patch("gen3release.env_cli.time")
@patch("gen3release.env_cli.copy_all_files")
@patch("gen3release.env_cli.Env")
def test_copy(mocked_env, copy_files, mocked_time, mocked_Gh, setUp_tearDown):
    """
    Test that pygithub methods are feed with correct arguments
    """
    args_pr = Namespace(
        source=ABS_PATH + "/data/fake_source_env",
        env=ABS_PATH + "/data/temp_target_env",
        pr_title="A pr title",
    )
    copy_files.return_value = ["file_1", "file_2"]
    mocked_time.time.return_value = "10.0"
    mocked_env.return_value.repo_dir = "./data"
    mocked_env.return_value.name = "env"
    env_cli.copy(args_pr)
    assert mocked_env.call_args_list == [call(args_pr.source), call(args_pr.env)]
    mocked_Gh.assert_called_with(repo="data")
    mocked_Gh.return_value.cut_new_branch.assert_called_once()
    mocked_Gh.return_value.create_pull_request_copy.assert_called_with(
        mocked_Gh.return_value.get_github_client.return_value,
        mocked_env(),
        mocked_env(),
        ["file_1", "file_2"],
        args_pr.pr_title,
        "copying files from env to env",
        "chore/promote_env_10",
    )


def test_copy_all_files(setUp_tearDown):

    with pytest.raises(NameError):
        s = Env("./fakepath")
        t = Env("./fakepath")
        env_cli.copy_all_files(s, t)

    src = Env(ABS_PATH + "/data/fake_source_env")
    tgt = Env(ABS_PATH + "/data/temp_target_env")
    files = env_cli.copy_all_files(src, tgt)
    expected_files = [
        "portal/gitops-sponsors/nhlbi.png",
        "portal/gitops-logo.png",
        "portal/gitops-favicon.ico",
        "portal/gitops.css",
        "portal/gitops.json",
        "etlMapping.yaml",
        "manifest.json",
        "manifests/fence/fence-config-public.yaml",
        "manifests/hatchery/hatchery.json",
    ]
    assert sorted(files) == sorted(expected_files)
