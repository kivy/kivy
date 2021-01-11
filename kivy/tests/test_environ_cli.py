# coding=utf-8

import itertools
from functools import partial
from os import environ
import shlex
import subprocess
import sys

import pytest

ENV_NAME="KIVY_NO_ARGS"
EXPECTED_STR = "Kivy Usage"


TRUTHY = {'true', '1', 'yes'}
FALSY = {'false', '0', 'no', "anything-else"}

SAMPLE_VALUES = {
    *TRUTHY, *FALSY
}

def _patch_env(**kw):
    env = {
        k: v
        for k, v in environ.items()
        if "kivy" not in k.lower()
    }

    env.update(**kw)
    return env

def _kivy_subproces_import(env):
    return subprocess.check_output(
        shlex.split(f"{sys.executable} -c 'import kivy' --help"),
        stderr=subprocess.PIPE,
        env=env
    ).decode("utf8")


@pytest.mark.parametrize("value", SAMPLE_VALUES)
def test_env_exist(value):
    env = _patch_env(**{ENV_NAME:value})
    stdout = _kivy_subproces_import(env)

    if value.lower() in TRUTHY:
        assert EXPECTED_STR not in stdout
    else:
        assert EXPECTED_STR in stdout

def test_env_not_exist():
    env = _patch_env()
    stdout = _kivy_subproces_import(env)
    assert EXPECTED_STR in stdout
