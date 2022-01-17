#!/usr/bin/env python

import os
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, "./src/")
from config import load_config

os.environ["TASKCALRC"] = os.path.realpath("./taskcal.yml")
os.environ["XDG_CONFIG_HOME"] = "/tmp"


def test_nonexistent_config(monkeypatch, tmp_path):
    monkeypatch.setenv("TASKCALRC", str(tmp_path / "not_a_file"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "not_a_dir"))

    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config == {}


def test_loading_config_via_arg(monkeypatch, tmp_path, project_root):
    monkeypatch.setenv("TASKCALRC", str(tmp_path / "not_a_file"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "not_a_dir"))

    source_config = project_root / "taskcal.yml"

    monkeypatch.chdir(tmp_path)

    config = load_config(source_config)

    with open(source_config) as f:
        config2 = yaml.safe_load(f)

    assert config == config2


def test_loading_default_config(monkeypatch, tmp_path, project_root):
    monkeypatch.setenv("TASKCALRC", str(tmp_path / "not_a_file"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "not_a_dir"))

    source_config = project_root / "taskcal.yml"

    shutil.copy(source_config, tmp_path)

    monkeypatch.chdir(tmp_path)

    config = load_config()

    with open(source_config) as f:
        config2 = yaml.safe_load(f)

    assert config == config2


def test_loading_config_via_env_var(
    monkeypatch, tmp_path_factory, project_root
):

    working_dir = tmp_path_factory.mktemp("working_dir")
    config_dir = tmp_path_factory.mktemp("config_dir")

    monkeypatch.setenv("TASKCALRC", str(config_dir / "taskcal.yml"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(working_dir / "not_a_dir"))

    source_config = project_root / "taskcal.yml"

    shutil.copy(source_config, config_dir)

    monkeypatch.chdir(working_dir)

    config = load_config()

    with open(source_config) as f:
        config2 = yaml.safe_load(f)

    assert config == config2


def test_loading_config_via_xdg_config(
    monkeypatch, tmp_path_factory, project_root
):
    working_dir = tmp_path_factory.mktemp("working_dir")
    config_dir = tmp_path_factory.mktemp("config_dir")

    monkeypatch.delenv("TASKCALRC")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_dir))

    config_dir.joinpath("taskcal").mkdir()

    source_config = project_root / "taskcal.yml"

    shutil.copy(source_config, config_dir / "taskcal/config.yml")

    monkeypatch.chdir(working_dir)

    config = load_config()

    with open(source_config) as f:
        config2 = yaml.safe_load(f)

    assert config == config2
