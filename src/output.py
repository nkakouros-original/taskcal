#!/usr/bin/env python

# TODO validate config options for outputs

import os
from abc import ABC, abstractmethod

import caldav
from icalendar import Calendar

from taskcal import icalendar_defaults


def resolve_output(type):
    if type == "ics":
        return ICSOutput
    if type == "caldav":
        return CaldavOutput

    raise ValueError(f"invalid output type: {type}")


class Output(ABC):
    def __init__(self, config):
        for k, v in config.items():
            setattr(self, k, v)

    @abstractmethod
    def sync(self, calendars):
        if not getattr(self, "enabled", True):
            return False

        return True


class ICSOutput(Output):
    def __init__(self, config):
        self.dir = os.path.realpath(config["dir"])

    def sync(self, calendars):
        os.makedirs(self.dir, exist_ok=True)

        for calendar, content in calendars.items():
            with open(f"{self.dir}/{calendar}.ics", "wb") as f:
                f.write(content.to_ical())


class CaldavOutput(Output):
    def sync(self, calendars):
        dav = caldav.DAVClient(
            self.host,
            username=self.username,
            password=self.password,
        ).principal()

        dav_cals = dav.calendars()
        dav_cal_names = [x.name for x in dav_cals]

        for calname, calendar in calendars.items():
            try:
                index = dav_cal_names.index(
                    calendar["NAME"] if "NAME" in calendar else calname
                )
                davcal = dav_cals[index]
            except ValueError:
                davcal = dav.make_calendar(name=calname)

            for event in calendar.walk(name="VTODO"):
                temp_cal = Calendar(calendar)
                temp_cal.add_component(event)
                davcal.save_event(temp_cal.to_ical())
