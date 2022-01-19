import pytest
import os
from unittest.mock import Mock, patch, call

from gen3release.gith.git import Git as Gen3releaseGit
from github.Repository import Repository
from gen3release.config import env
from tests.conftest import target_env

ABS_PATH = os.path.abspath(".")


@pytest.fixture()
def ghub():
    return Gen3releaseGit(repo="cdis-manifest")


@pytest.fixture()
def mock_repo():
    return Mock(spec=Repository)


@patch("gen3release.gith.git.Github")
def test_get_github_client(mocked_gh, ghub):
    """
    Test the Git object is initialized with right values
    """
    ghub.get_github_client()
    mocked_gh.assert_called_with("MEH-123")
    mocked_gh.return_value.get_organization.assert_called_with("uc-cdis")
    mocked_gh.return_value.get_organization.return_value.get_repo.assert_called_with(
        "cdis-manifest"
    )


def test_cut_new_branch(ghub, mock_repo):
    """
    Test pygithub methods receive proper arguments
    """
    mock_repo.get_branch = Mock()
    git_ref = ghub.cut_new_branch(mock_repo, "new_branch_name")
    mock_repo.get_branch.assert_called_with("master")
    mock_repo.create_git_ref.assert_called_with(
        ref="refs/heads/new_branch_name", sha=mock_repo.get_branch().commit.sha
    )


def test_create_pull_request_copy(ghub, target_env, mock_repo):
    """
    Test pygithub methods receive proper arguments
    """
    ghub.create_pull_request_copy(
        mock_repo,
        target_env,
        ["etlMapping.yaml", "manifest.json"],
        "testpr",
        "commit message",
        "new_branch_name",
    )

    # Compare expected args for get_contents method
    expected_args = [
        call("fake_target_env/etlMapping.yaml", "new_branch_name"),
        call("fake_target_env/manifest.json", "new_branch_name"),
    ]
    assert expected_args == mock_repo.get_contents.call_args_list

    # Compare expected args for update_file method
    data1 = open(f"{ABS_PATH}/data/fake_target_env/etlMapping.yaml", "rb")
    data2 = open(f"{ABS_PATH}/data/fake_target_env/manifest.json", "rb")
    expect_args = [
        call(
            "fake_target_env/etlMapping.yaml",
            "copying etlMapping.yaml to fake_target_env",
            data1.read(),
            mock_repo.get_contents().sha,
            branch="new_branch_name",
        ),
        call(
            "fake_target_env/manifest.json",
            "copying manifest.json to fake_target_env",
            data2.read(),
            mock_repo.get_contents().sha,
            branch="new_branch_name",
        ),
    ]
    data1.close()
    data2.close()
    assert expect_args == mock_repo.update_file.call_args_list

    mock_repo.create_pull.assert_called_with(
        title="testpr", body="commit message", head="new_branch_name", base="master"
    )


def test_create_pull_request_apply(ghub, mock_repo, target_env):
    """
    Test pygithub methods receive proper arguments
    """
    ghub.create_pull_request_apply(
        mock_repo,
        "202020",
        target_env,
        ["manifest.json", "manifests/hatchery/hatchery.json"],
        "prtitle",
        ["label1"],
        "commit message",
        "new_branch_name",
    )
    expected_args = [
        call("fake_target_env/manifest.json", "new_branch_name"),
        call("fake_target_env/manifests/hatchery/hatchery.json", "new_branch_name"),
    ]
    assert expected_args == mock_repo.get_contents.call_args_list

    # Compare expected args for update_file method
    data1 = open(f"{ABS_PATH}/data/fake_target_env/manifest.json", "rb")
    data2 = open(
        f"{ABS_PATH}/data/fake_target_env/manifests/hatchery/hatchery.json", "rb"
    )

    expect_args = [
        call(
            "fake_target_env/manifest.json",
            "apply version 202020 to fake_target_env",
            data1.read(),
            mock_repo.get_contents().sha,
            branch="new_branch_name",
        ),
        call(
            "fake_target_env/manifests/hatchery/hatchery.json",
            "apply version 202020 to fake_target_env",
            data2.read(),
            mock_repo.get_contents().sha,
            branch="new_branch_name",
        ),
    ]
    data1.close()
    data2.close()
    assert expect_args == mock_repo.update_file.call_args_list
