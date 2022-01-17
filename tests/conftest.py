#!/usr/bin/env python

import pathlib
import shutil

import pytest
import tasklib

# TODO use tmp_dir or sth else
tw_dir = ".tmp"


@pytest.fixture
def tw():
    def _create_task(task: dict = None):
        tw = tasklib.TaskWarrior(data_location=tw_dir)
        if task:
            tw_task = tasklib.Task(tw, **task)
            tw_task.save()

            return tw_task

    yield _create_task

    shutil.rmtree(tw_dir)


@pytest.fixture
def project_root():
    return pathlib.Path(__file__).resolve().parent.parent
