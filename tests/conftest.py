#!/usr/bin/env python

import shutil

import pytest
import tasklib

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
