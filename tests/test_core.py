#!/usr/bin/env python

# TODO
# use fixtures for tw loading

import datetime
import os
import sys

import pytest
from icalendar import Calendar

from .conftest import tw_dir

sys.path.insert(0, "./src/")
from taskcal import Taskcal, date_associations, priorities, simple_associations


def compare(task, todo):
    specially_handled = ["categories"]

    message = "Todo:{prop} == TaskWarrior:{attr}"
    for assoc in [
        assoc
        for assoc in simple_associations
        if assoc.attr in task and assoc.prop not in specially_handled
    ]:
        assert todo[assoc.prop] == task[assoc.attr], message.format(
            attr=assoc.attr, prop=assoc.prop
        )

    for assoc in [assoc for assoc in date_associations if assoc.attr in task]:
        assert todo[assoc.prop].dt == task[assoc.attr], message.format(
            attr=assoc.attr, prop=assoc.prop
        )

    if task["tags"]:
        assert "categories" in todo
        assert set(todo["categories"].cats) == task["tags"], message.format(
            attr="tags", prop="categories"
        )

    if task["priority"]:
        assert todo["priority"] == priorities[task["priority"]]


def test_failed_initialization():
    with pytest.raises(TypeError) as exception:
        Taskcal()
    assert (
        str(exception.value) == "no taskwarrior data dir or taskrc path given"
    )

    with pytest.raises(FileNotFoundError):
        Taskcal(tw_data_dir="/not-existing")
    with pytest.raises(FileNotFoundError):
        Taskcal(tw_rc="/not-existing")

    with pytest.raises(NotADirectoryError) as exception:
        Taskcal(tw_data_dir=os.path.realpath(__file__))
    assert (
        str(exception.value)
        == f"'{os.path.realpath(__file__)}' is not a directory"
    )

    with pytest.raises(FileNotFoundError) as exception:
        Taskcal(tw_rc=os.path.dirname(os.path.realpath(__file__)))
    assert (
        str(exception.value)
        == f"'{os.path.dirname(os.path.realpath(__file__))}' is not a file"
    )


def test_successful_initialization(tw):
    tw()

    with pytest.raises(TypeError) as exception:
        Taskcal(tw_data_dir="path", tw_rc="path")
    assert (
        str(exception.value)
        == "only one of 'tw_data_dir' and 'tw_rc' must be given"
    )

    tc = Taskcal(tw_data_dir=tw_dir)
    assert tc.tw.config["data.location"] == tw_dir

    with open(tw_dir + "/taskrc", "w+") as f:
        f.write(f"data.location={tw_dir}/subfolder")
    tc = Taskcal(tw_rc=tw_dir + "/taskrc")
    assert tc.tw.config["data.location"] == tw_dir + "/subfolder"


def test_empty_calendar_when_no_tasks(tw):
    tw()

    tc = Taskcal(tw_data_dir=tw_dir)

    assert len(tc.calendars) == 1
    assert "<noname>" in tc.calendars
    assert len(tc.calendars["<noname>"].subcomponents) == 0
    assert "X-WR-CALNAME" not in tc.calendars


def test_task_with_simple_associations(tw):
    task = tw(
        {"description": "one task", "tags": ["tag1", "tag2"], "priority": "H"}
    )

    tc = Taskcal(tw_data_dir=tw_dir)

    assert len(tc.calendars) == 1
    assert len(tc.calendars["<noname>"].subcomponents) == 1
    compare(task, tc.calendars["<noname>"].subcomponents[0])


def test_priority_association(tw):
    for twp, icalp in priorities.items():
        tw({"description": "task", "priority": twp})

        tc = Taskcal(tw_data_dir=tw_dir)

        tc.calendars["<noname>"].subcomponents[0]["priority"] == icalp


def test_task_with_changing_status(tw):
    task = tw({"description": "task"})

    tc = Taskcal(tw_data_dir=tw_dir)

    assert tc.calendars["<noname>"].subcomponents[0]["status"] == "needs-action"

    task["wait"] = datetime.datetime.now() + datetime.timedelta(5)
    assert tc.calendars["<noname>"].subcomponents[0]["status"] == "needs-action"

    task.start()
    assert tc.calendars["<noname>"].subcomponents[0]["status"] == "in-process"

    task.done()
    assert tc.calendars["<noname>"].subcomponents[0]["status"] == "completed"

    task.delete()
    assert tc.calendars["<noname>"].subcomponents[0]["status"] == "cancelled"


def test_task_with_dependencies(tw):
    task1 = tw({"description": "task1"})
    task2 = tw({"description": "task2"})
    task3 = tw({"description": "task3"})
    task3["depends"] = set([task1, task2])
    task3.save()

    dependency_list = set([task1["uuid"], task2["uuid"]])

    tc = Taskcal(tw_data_dir=tw_dir)

    assert len(tc.calendars["<noname>"].subcomponents) == 3
    assert len(tc.calendars["<noname>"].subcomponents[-1]["related-to"]) == 2
    assert (
        set(tc.calendars["<noname>"].subcomponents[-1]["related-to"])
        == dependency_list
    )


def test_task_with_project(tw):
    task = tw({"description": "task with project", "project": "project1"})

    tc = Taskcal(tw_data_dir=tw_dir)

    assert len(tc.calendars) == 1
    assert "project1" in tc.calendars
    assert tc.calendars["project1"]["X-WR-CALNAME"] == "project1"
    assert len(tc.calendars["project1"].subcomponents) == 1


def test_task_with_dates(tw):
    wait = datetime.datetime.now() + datetime.timedelta(1)
    scheduled = datetime.datetime.now() + datetime.timedelta(2)
    due = datetime.datetime.now() + datetime.timedelta(3)
    until = datetime.datetime.now() + datetime.timedelta(4)

    task = tw(
        {
            "description": "task3",
            "wait": wait,
            "scheduled": scheduled,
            "due": due,
            "until": until,
        },
    )

    tc = Taskcal(tw_data_dir=tw_dir)

    compare(task, tc.calendars["<noname>"].subcomponents)


def test_default_filter(tw):
    task = tw({"description": "task"})
    tc = Taskcal(tw_data_dir=tw_dir)

    assert len(tc.calendars["<noname>"].subcomponents) == 1

    task.done()

    assert len(tc.calendars["<noname>"].subcomponents) == 1


def test_overriding_filter(tw):
    task = tw({"description": "task"})
    tc = Taskcal(tw_data_dir=tw_dir, filter="status:pending")

    assert len(tc.calendars["<noname>"].subcomponents) == 1

    task.done()

    assert len(tc.calendars["<noname>"].subcomponents) == 0


def test_ics_file_generation(tw):
    task1 = tw({"description": "task 1", "project": "project1"})
    task2 = tw({"description": "task 2", "project": "project1"})

    task3 = tw(
        {
            "description": "task3",
            "project": "project1",
        },
    )
    task3["depends"] = set([task1, task2])
    task3.save()

    task4 = tw({"description": "task 1"})

    os.environ["TASKDATA"] = tw_dir

    import runpy
    import sys

    old_argv = sys.argv
    sys.argv = [old_argv[0]]
    runpy.run_module(Taskcal.__module__, run_name="__main__")
    sys.argv = old_argv

    with open("project1.ics") as f:
        ics = Calendar.from_ical(f.read())

    todos = ics.walk(name="vtodo")
    compare(task1, todos[0])
    compare(task2, todos[1])
    compare(task3, todos[2])

    with open("<noname>.ics") as f:
        ics = Calendar.from_ical(f.read())

    compare(task4, ics.walk(name="vtodo")[0])


def test_output_folder_option(tw):
    task = tw({"description": "task 1", "project": "project1"})

    import runpy
    import sys

    out_folder = ".tmp"

    os.environ["TASKDATA"] = tw_dir
    old_argv = sys.argv
    sys.argv = [old_argv[0], "--output-folder", out_folder]
    runpy.run_module(Taskcal.__module__, run_name="__main__")
    sys.argv = old_argv

    with open(f"{out_folder}/project1.ics") as f:
        ics = Calendar.from_ical(f.read())

    todos = ics.walk(name="vtodo")
    compare(task, todos[0])
