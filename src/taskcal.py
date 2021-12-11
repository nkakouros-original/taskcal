#!/usr/bin/env python

# TODO
# set custom prodid
# apply tw filter in Taskcal's constructor already

import os
from collections import namedtuple
from pathlib import Path
from typing import DefaultDict, Dict

from icalendar import Calendar, Todo
from tasklib import Task, TaskWarrior
from tasklib.filters import TaskWarriorFilter

icalendar_defaults = {
    "version": "2.0",
    "prodid": "-//SabreDAV//SabreDAV//EN",
    "calscale": "gregorian",
}

# Taskwarrior attributes to icalendar properties
Assoc = namedtuple("Assoc", ["attr", "prop"])
simple_associations = frozenset(
    [
        Assoc("uuid", "uid"),
        Assoc("description", "summary"),
        Assoc("tags", "categories"),
    ]
)
date_associations = frozenset(
    [
        Assoc("modified", "dtstamp"),
        Assoc("end", "completed"),
        Assoc("due", "due"),
        Assoc("scheduled", "start"),
    ]
)
direct_associations = simple_associations | date_associations

other_associations = frozenset(
    [
        Assoc("priority", "priority"),
        Assoc("depends", "related-to"),
        Assoc("status", "status"),
    ]
)

priorities = {"H": 0, "M": 5, "L": 9}


class Taskcal:
    def __init__(
        self,
        *,
        tw_rc: str = None,
        tw_data_dir: str = None,
        filter: str = "status.any:",
    ) -> None:

        # When tasklib runs taskwarrior commands, it overrides the data.location
        # settings if the user sets it to a custom value in the TaskWarrior
        # constructor. It also sets TASKRC to a custom value if the user sets
        # that too in the constructor. If only one of the two (or none of the
        # two) is set by the user, the taskwarrior command will do its own
        # resolution of the data location based on, among others, the env
        # variables TASKDATA and TASKRC. To be sure that when I use
        # `tw_data_dir` or `tw_rc` in this constructor I will always use the
        # intended path, I unset these env variables.
        os.environ.pop("TASKDATA", None)
        os.environ.pop("TASKRC", None)

        if tw_data_dir and tw_rc:
            raise TypeError(
                "only one of 'tw_data_dir' and 'tw_rc' must be given"
            )
        elif tw_data_dir:
            if not Path(tw_data_dir).exists():
                raise FileNotFoundError
            if not Path(tw_data_dir).is_dir():
                raise NotADirectoryError(f"'{tw_data_dir}' is not a directory")
            self.tw = TaskWarrior(data_location=tw_data_dir)
        elif tw_rc:
            if not Path(tw_rc).exists():
                raise FileNotFoundError
            if not Path(tw_rc).is_file():
                raise FileNotFoundError(f"'{tw_rc}' is not a file")
            self.tw = TaskWarrior(taskrc_location=tw_rc)
        else:
            raise TypeError("no taskwarrior data dir or taskrc path given")

        self.filter = TaskWarriorFilter(self.tw)
        self.filter.add_filter(filter)

    @property
    def calendars(self) -> Dict[str, Calendar]:
        calendars: DefaultDict[str, Calendar] = DefaultDict(
            lambda: Calendar(icalendar_defaults)
        )

        tasks = self.tw.filter_tasks(self.filter)

        if not tasks:
            # Initialize the default calendar
            calendars["<noname>"]

        for task in tasks:
            task.refresh()

            todo = Todo()

            for assoc in direct_associations:
                if task[assoc.attr]:
                    todo.add(assoc.prop, task[assoc.attr])

            if task["priority"]:
                todo.add("priority", priorities.get(task["priority"]))

            todo.add("status", self.get_tw_task_status(task))

            for dependency in task["depends"] or []:
                todo.add("related-to", dependency["uuid"])

            calendars[task["project"] or "<noname>"].add_component(todo)

        for calname, calendar in calendars.items():
            if calname == "<noname>":
                continue
            calendar.add("X-WR-CALNAME", calname)
            calendar.add("NAME", calname)

        return dict(calendars)

    @staticmethod
    def get_tw_task_status(task: Task) -> str:
        if task.active:
            return "in-process"
        elif task.completed:
            return "completed"
        elif task.deleted:
            return "cancelled"
        else:  # pending/waiting
            return "needs-action"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--output-folder",
        type=str,
        help="folder to generate ics files in",
        default=".",
    )
    args = parser.parse_args()

    output_folder = os.path.realpath(args.output_folder)
    os.makedirs(output_folder, exist_ok=True)

    tw_data_location = os.getenv("TASKDATA", "~/.task")

    tc = Taskcal(tw_data_dir=tw_data_location)

    for calendar, content in tc.calendars.items():
        with open(f"{output_folder}/{calendar}.ics", "wb") as f:
            f.write(content.to_ical())
