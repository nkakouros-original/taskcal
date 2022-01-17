#!/usr/bin/env python

import os
import sys
from pathlib import Path

import caldav
import pytest
from icalendar import Calendar, Todo

from .conftest import tw_dir

sys.path.insert(0, "./src/")

from output import CaldavOutput, ICSOutput, Output, resolve_output
from taskcal import icalendar_defaults


def test_resolve_output():
    assert resolve_output("ics") == ICSOutput
    assert resolve_output("caldav") == CaldavOutput

    with pytest.raises(ValueError) as exception:
        resolve_output("not-a-type")
    assert str(exception.value) == "invalid output type: not-a-type"


def test_abstract_class_instantiation():
    with pytest.raises(TypeError) as exception:
        Output()
    assert "abstract method sync" in str(exception.value)


def test_abstract_class_constructor():
    class Tester(Output):
        def sync(self, calendars):
            pass

    config = {"one": 1, "two": 2}
    t = Tester(config)

    assert Tester({})
    assert t.one == 1
    assert t.two == 2


def test_abstract_class_sync_enabled():
    class Tester(Output):
        def sync(self, calendars):
            return super().sync(calendars)

    t = Tester({"enabled": False})

    assert not t.sync([])


def test_abstract_class_sync_disableed():
    class Tester(Output):
        def sync(self, calendars):
            return super().sync(calendars)

    t = Tester({})

    assert t.sync([])


def test_ics_output(tmp_path):
    calendars = {}
    projects = {}
    for index in range(1, 3):
        tasks = []
        tasks.append({"summary": f"Todo {2*index-1}"})
        tasks.append({"summary": f"Todo {2*index}"})
        projects[index] = tasks

        calendar = Calendar({"NAME": f"Calendar {index}"})
        calendar.add_component(Todo({"summary": f"Todo {2*index-1}"}))
        calendar.add_component(Todo({"summary": f"Todo {2*index}"}))
        calendars[f"calendar-{index}"] = calendar

    output = ICSOutput({"dir": tmp_path})
    output.sync(calendars)

    for index in range(1, 3):
        ics_file = tmp_path / f"calendar-{index}.ics"
        assert Path(ics_file).is_file()

        with open(ics_file) as f:
            ics = Calendar.from_ical(f.read())

        for task_number, todo in enumerate(ics.walk(name="VTODO")):
            assert projects[index]
            assert todo["summary"] == projects[index][task_number]["summary"]


def test_caldav_output(mocker):
    calendars = {}
    for index in range(0, 3):
        calendar = Calendar({"NAME": f"Calendar {index}"} if index else {})
        calendar.update(icalendar_defaults)
        calendar.add_component(Todo({"summary": f"Todo {2*index}"}))
        calendar.add_component(Todo({"summary": f"Todo {2*index+1}"}))
        calendars[f"calendar-{index}"] = calendar

    mocker.patch("caldav.DAVClient", name="DAVClient")

    davclient_return = mocker.Mock(name="DAVClient return")
    caldav.DAVClient.return_value = davclient_return

    save_event_mock = mocker.Mock(name="add_event", return_value=True)
    calendar_mock = mocker.Mock(name="calendar", save_event=save_event_mock)
    make_calendar_mock = mocker.Mock(
        name="make_calendar", return_value=calendar_mock
    )
    calendars_mock = mocker.Mock(
        name="calendars",
        return_value=[
            type(
                "c", (), {"name": "calendar-0", "save_event": save_event_mock}
            )(),
            type(
                "c", (), {"name": "Calendar 1", "save_event": save_event_mock}
            )(),
        ],
    )
    principal_mock = mocker.Mock(
        name="principal",
        calendars=calendars_mock,
        make_calendar=make_calendar_mock,
    )
    davclient_return.principal.return_value = principal_mock

    mocker.seal(caldav.DAVClient)

    output = CaldavOutput(
        {"host": "localhost", "username": "demo", "password": "demo"}
    )
    output.sync(calendars)

    save_event_calls = [call.args[0] for call in save_event_mock.call_args_list]
    for index in range(0, 3):
        calendar = Calendar()
        todo1 = Calendar.from_ical(save_event_calls[2 * index])
        calendar.update(todo1)  # updates only calendar props
        calendar.subcomponents.extend(todo1.subcomponents)
        calendar.subcomponents.extend(
            Calendar.from_ical(save_event_calls[2 * index + 1]).subcomponents
        )

        assert calendars[f"calendar-{index}"] == calendar
        for subcomponent in calendar.subcomponents:
            assert subcomponent in calendars[f"calendar-{index}"].subcomponents
