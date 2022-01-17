#!/usr/bin/env python

import sys

sys.path.insert(0, "./src/")
import cli
import output


def test_cli_run(mocker):
    import runpy
    import sys

    mocker.patch(
        "config.load_config",
        return_value={"outputs": [{"type": "output_type"}]},
    )

    taskcal_mock = mocker.Mock(name="taskcal", calendars=["cal1", "cal2"])
    mocker.patch("taskcal.Taskcal", return_value=taskcal_mock)

    sync_mock = mocker.Mock(name="sync")
    output_function_mock = mocker.Mock(
        name="output_function", return_value=sync_mock
    )
    mocker.patch("output.resolve_output", return_value=output_function_mock)

    mocker.seal(output)

    old_argv = sys.argv
    sys.argv = ["taskcal"]
    runpy.run_module("cli", run_name="__main__")
    sys.argv = old_argv

    assert sync_mock.sync.call_args_list[0].args[0] == taskcal_mock.calendars
