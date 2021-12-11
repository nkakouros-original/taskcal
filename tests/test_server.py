#!/usr/env/bin python

import os
import sys

import icalendar
import pytest

from .conftest import tw_dir

os.environ["TASKDATA"] = tw_dir

sys.path.insert(0, "./src/")
from taskcal_server import app


@pytest.fixture
def client(tw):
    def _return(task=None):
        tw(task)
        return app.test_client()

    return _return


def test_non_existent_taskwarrior():
    response = app.test_client().get("/nonexistent.ics")

    assert response.status_code == 500
    assert response.data == b"nonexistent TaskWarrior db"


def test_non_existent_calendar(client):
    response = client().get("/nonexistent.ics")

    assert response.status_code == 404
    assert response.data == b"no such calendar"


def test_calendar_export(client):
    task1 = {"description": "task1"}
    response = client(task1).get("/<noname>.ics")

    assert response.status_code == 200

    ics = icalendar.Calendar.from_ical(response.data)

    todos = ics.walk(name="VTODO")
    assert len(todos) == 1
    assert (todos[0]["SUMMARY"]) == "task1"
