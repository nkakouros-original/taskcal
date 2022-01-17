#!/usr/bin/env python


def test_ics_file_generation(tw):
    task1 = tw({"description": "task 1", "project": "project1"})
    task2 = tw({"description": "task 2", "project": "project1"})

    task3 = tw({"description": "task3", "project": "project1"})
    task3["depends"] = set([task1, task2])
    task3.save()

    task4 = tw({"description": "task 1"})

    os.environ["TASKDATA"] = tw_dir

    output = ICSOutput()
    output.sync()

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
