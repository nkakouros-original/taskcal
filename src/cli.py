#!/usr/bin/env python

if __name__ == "__main__":

    import argparse
    import os

    from config import load_config
    from output import resolve_output
    from taskcal import Taskcal

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="path to the configuration file",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    tw_data_location = os.getenv("TASKDATA", "~/.task")

    tc = Taskcal(tw_data_dir=tw_data_location)

    for output_config in config["outputs"]:
        output = resolve_output(output_config["type"])(output_config)
        output.sync(tc.calendars)
