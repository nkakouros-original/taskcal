#!/usr/bin/env python

import os

from flask import Flask, Response
from gevent.pywsgi import WSGIServer

from taskcal import Taskcal

app = Flask(__name__)

tw_data_location = os.getenv("TASKDATA", "~/.task")


@app.route("/<calendar>.ics")
def stream_ics_files(calendar):
    def generate(calendar):
        try:
            tc = Taskcal(tw_data_dir=tw_data_location)
        except FileNotFoundError:
            return None

        try:
            icalendar = [
                content
                for calname, content in tc.calendars.items()
                if calname == calendar
            ].pop()
        except IndexError:
            return ""

        return icalendar.to_ical()

    if (body := generate(calendar)) is None:
        response = Response(
            "nonexistent TaskWarrior db", status=500, mimetype="text/plain"
        )
    elif not (body := generate(calendar)):
        response = Response(
            "no such calendar", status=404, mimetype="text/plain"
        )
    else:
        response = Response(body, mimetype="text/calendar")
        response.headers.add(
            "Content-Disposition", f"attachment; filename={calendar}.ics"
        )

    return response


if __name__ == "__main__":  # pragma: no cover
    http_server = WSGIServer(("", 5000), app)
    http_server.serve_forever()
