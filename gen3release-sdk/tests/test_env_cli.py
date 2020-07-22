from gen3release import env_cli
import pytest
import json
import os
import argparse
from argparse import Namespace

fullpath_wd = os.path.abspath(".")


def test_make_parser():
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


def test_copy():
    import filecmp
    import os.path

    def are_dir_trees_equal(dir1, dir2):
        """
        Compare two directories recursively. Files in each directory are
        assumed to be equal if their names and contents are equal.
    """
        dirs_cmp = filecmp.dircmp(dir1, dir2)
        if (
            len(dirs_cmp.left_only) > 0
            or len(dirs_cmp.right_only) > 0
            or len(dirs_cmp.funny_files) > 0
        ):
            return False
        (_, mismatch, errors) = filecmp.cmpfiles(
            dir1, dir2, dirs_cmp.common_files, shallow=False
        )
        if len(mismatch) > 0 or len(errors) > 0:
            return False
        for common_dir in dirs_cmp.common_dirs:
            new_dir1 = os.path.join(dir1, common_dir)
            new_dir2 = os.path.join(dir2, common_dir)
            if not are_dir_trees_equal(new_dir1, new_dir2):
                return False
        return True

    os.system(f"mkdir {fullpath_wd}/temp")
    args = Namespace(
        source=fullpath_wd + "/data/test_environment.$$&",
        env=fullpath_wd + "/temp",
        pr_title="",
    )
    env_cli.copy(args)
    assert are_dir_trees_equal(args.source, args.env)
    os.system(f"rm -r {fullpath_wd}/temp")
