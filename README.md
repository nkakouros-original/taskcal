# Taskcal

A python script to export your pending TaskWarrior tasks into icalendar files (.ics).

These can be imported to conventional calendaring applications. The script will
create one ics file per TaskWarrior project, so that when you import the files to
your calendar app, each project will have its own calendar. There is no support
for the reverse (i.e. icalendar -> TaskWarrior) yet, although it is in the backlog.

TaskWarrior attributes that get exported currently:

- description
- uuid
- tags
- priority
- dependencies
- status
- due date
- scheduled date
- modified date
- end date

## Installation

There is currently no pip package for taskcal.

Run:

```
pip install -r requirements.txt
```

and download the script file ([src/taskcal.py](src/taskcal.py)).
