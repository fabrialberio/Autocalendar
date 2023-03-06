from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from json import load, dump

from .google_calendar import Event, Calendar, get_calendar_service, HttpError
from .mastercom import MastercomAPI, Assignment, AssignmentType


ADDED_EVENTS_PATH = Path('config/added_events.json')


def body_from_assignment(assignment: Assignment) -> dict:
    color_id = 0
    summary = ''
    description = ''

    if assignment.kind == AssignmentType.TEST:
        description = ', '.join(i for i in [assignment.title, assignment.description] if i)
        summary = description.replace('\n', ' ').replace('\r', ' ').capitalize()
    elif assignment.kind == AssignmentType.HOMEWORK:
        description = assignment.description
        summary = ': '.join(i for i in [assignment.subject.capitalize(), assignment.description] if i) \
            .replace('\n', ' ').replace('\r', ' ')
    elif assignment.kind == AssignmentType.TIMETABLE:
        summary = assignment.subject.capitalize()

    if assignment.kind in [AssignmentType.TEST, AssignmentType.HOMEWORK]: # All-day events
        start = {'date': assignment.start.date().isoformat()}
        end = {'date': (assignment.start.date() + timedelta(days=1)).isoformat()}
    else: # In-day events
        start = {'dateTime': assignment.start.isoformat()}
        end = {'dateTime': assignment.end.isoformat()}

    return {
        'summary': summary,
        'description': description + f' (Aggiunto il  {datetime.now().strftime("%D")})',

        'start': start,
        'end':   end,

        'colorId': color_id,
        'transparency': 'transparent'}


class AddResult(Enum):
    ADD = 'add'
    SKIP = 'skip'
    PATCH = 'patch'


@dataclass
class CalendarAdder:
    calendar: Calendar
    mastercom: MastercomAPI
    result_tally: dict = field(default_factory=lambda: {
        AddResult.ADD: [],
        AddResult.SKIP: [],
        AddResult.PATCH: []})

    @classmethod
    def from_tokens(cls, mastercom_token_path: Path, google_token_path: Path, calendar_id: str):
        with open(mastercom_token_path, 'r') as file:
            mastercom_dict = load(file)

        calendar = Calendar.from_id(get_calendar_service(google_token_path), calendar_id)
        mastercom = MastercomAPI(
            token=mastercom_dict['token'],
            mastercom_id=mastercom_dict['mastercom_id'],
            school_id=mastercom_dict['school_id'],
            student_id=mastercom_dict['student_id']
        )

        return CalendarAdder(calendar, mastercom)

    def add_assignment(self, assignment: Assignment, existing_event: 'Event | None'):
        body = body_from_assignment(assignment)

        if existing_event is not None:
            if body['summary'] == existing_event.summary and body['description'] == existing_event.description:
                self.result_tally[AddResult.SKIP].append(existing_event)
            else:
                existing_event.patch(body)
                self.result_tally[AddResult.PATCH].append(existing_event)
        else:
            existing_event = self.calendar.add(body)
            self.result_tally[AddResult.ADD].append(existing_event)

            with open(ADDED_EVENTS_PATH, 'r') as file:
                added_events = load(file)
                added_events[assignment.unique_id] = existing_event.id

            with open(ADDED_EVENTS_PATH, 'w') as file:
                dump(added_events, file, indent=True)

    def add_all(self,
            type: AssignmentType,
            only_future = True
        ):
        start = datetime.now() if only_future else None

        with open(ADDED_EVENTS_PATH, 'r') as file:
            added_events = load(file)

        if type == AssignmentType.TEST:
            assignments = self.mastercom.tests(start)
        elif type == AssignmentType.HOMEWORK:
            assignments = self.mastercom.homework(start)
        elif type == AssignmentType.TIMETABLE:
            raise NotImplementedError('Adding timetable is not implemented')
            assignments = self.mastercom.timetable(start)

        for a in assignments:
            event_id = added_events.get(a.unique_id)
            event = None

            if event_id is not None:
                try:
                    event = self.calendar.event(event_id)
                except HttpError:
                    pass

            self.add_assignment(a, event)

    def print_tally(self, compact = False):
        added: list = self.result_tally[AddResult.ADD]
        patched = self.result_tally[AddResult.PATCH]
        skipped = self.result_tally[AddResult.SKIP]

        def repr_events(events):
            return '\n'.join(f'  ⦁ {i.summary[:100]}' for i in events)

        print(f'Aggiungendo eventi a "{self.calendar.summary}"')
        if compact:
            print(f'Risultato: {len(added)} aggiunti, {len(patched)} aggiornati, {len(skipped)} saltati\n')
        else:
            print(f'''
Eventi aggiunti ({len(added)}):
{repr_events(added)}
Eventi aggiornati ({len(patched)}):
{repr_events(patched)}
Eventi saltati ({len(skipped)})
''')

    def remove_events(self, start: datetime, end: datetime):
        events: list = self.calendar.events()

        for e in events:
            event_date = datetime.fromisoformat(e.start['date'])

            if start < event_date < end:
                e.remove()