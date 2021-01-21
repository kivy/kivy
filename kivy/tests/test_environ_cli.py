# coding=utf-8

from os import environ
import shlex
import subprocess
import sys

import pytest

ENV_NAME = "KIVY_NO_ARGS"
KIVY_ENVS_TO_EXCLUDE = ("KIVY_UNITTEST", "KIVY_PACKAGING")

EXPECTED_STR = "Kivy Usage"

TRUTHY = {"true", "1", "yes"}
FALSY = {"false", "0", "no", "anything-else"}

SAMPLE_VALUES = {*TRUTHY, *FALSY}


def _patch_env(*filtered_keys, **kw):
    env = {k: v for k, v in environ.items() if k not in filtered_keys}
    env.update(kw)
    return env


def _kivy_subproces_import(env):
    return subprocess.run(
        [sys.executable, "-c", "import kivy", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    ).stdout.decode("utf8")


@pytest.mark.parametrize("value", SAMPLE_VALUES)
def test_env_exist(value):
    env = _patch_env(*KIVY_ENVS_TO_EXCLUDE, **{ENV_NAME: value})
    stdout = _kivy_subproces_import(env)

    if value in TRUTHY:
        assert EXPECTED_STR not in stdout
    else:
        assert EXPECTED_STR in stdout


def test_env_not_exist():
    env = _patch_env(ENV_NAME, *KIVY_ENVS_TO_EXCLUDE)
    stdout = _kivy_subproces_import(env)
    assert EXPECTED_STR in stdout
