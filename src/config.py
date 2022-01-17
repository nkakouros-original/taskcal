#!/usr/bin/env python

import os

import yaml


def load_config(config_file=None):
    config = {}

    taskcalrc = os.path.expanduser(
        config_file
        or os.path.isfile("./taskcal.yml")
        and "taskcal.yml"
        or os.getenv("TASKCALRC")
        or os.getenv("XDG_CONFIG_HOME", "~/.config") + "/taskcal/config.yml"
    )

    taskcalrc = os.path.realpath(taskcalrc)

    if os.path.isfile(taskcalrc):
        with open(taskcalrc, "r") as f:
            config.update(yaml.safe_load(f))

    return config
