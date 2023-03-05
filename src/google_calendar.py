# -*- coding: utf8 -*-
from dataclasses import dataclass
from pathlib import Path

from .google_api import GoogleAPI, GoogleAPIObject, Resource


API_SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']


def get_calendar_service(token_path: Path):
    google_api = GoogleAPI.from_token(token_path)
    return google_api.build('calendar', 'v3')


@dataclass(init=False)
class Event(GoogleAPIObject):
    kind: str
    etag: str
    id: str

    status: str
    htmlLink: str
    created: str
    updated: str
    summary: str
    description: str
    location: str
    colorId: str
    creator: dict
    organizer: dict

    start: dict
    end: dict
    endTimeUnspecified: bool
    recurrence: list
    recurringEventId: str
    originalStartTime: dict

    transparency: str
    visibility: str
    iCalUID: str
    sequence: int
    attendees: list
    attendeesOmitted: bool
    extendedProperties: dict
    hangoutLink: str
    conferenceData: dict
    gadget: dict
    anyoneCanAddSelf: bool
    guestsCanInviteOthers: bool
    guestsCanModify: bool
    guestsCanSeeOtherGuests: bool
    privateCopy: bool
    locked: bool
    reminders: dict
    source: dict
    attachments: list
    eventType: str

    @classmethod
    def from_id(cls, calendar: 'Calendar', id: str):
        '''Creates and updates an object by constructing an empty dict from the id'''
        event = cls(calendar, {'id': id})
        event._update()
        return event

    def __init__(self, calendar: 'Calendar', source_dict: dict) -> None:
        self._calendar = calendar
        self._service = calendar._service
        self._dict = source_dict
        super().__init__(self._service, source_dict)

    def remove(self):
        self._service.events().delete(calendarId=self._calendar.id, eventId=self.id).execute()
        del self

    def patch(self, body: dict) -> 'Event': 
        self._service.events().patch(calendarId=self._calendar.id, eventId=self.id, body=body).execute()
        self._update()
        return self

    def _update(self):
        self._dict = self._service.events().get(calendarId=self._calendar.id, eventId=self.id).execute()


class Calendar(GoogleAPIObject):
    kind: str
    etag: str
    id: str
    summary: str
    description: str
    location: str
    timeZone: str
    conferenceProperties: list

    @classmethod
    def from_google_API(cls, google_API: GoogleAPI, source_dict: dict):
        '''Builds a Google API service and creates a Calendar object using it'''
        service = google_API.build('calendar', 'v3')
        return cls(service, source_dict)

    @classmethod
    def from_google_API_and_id(cls, google_API: GoogleAPI, id: str):
        '''Creates an object from Google API and an ID'''
        service = google_API.build('calendar', 'v3')
        return cls.from_id(service, id)

    def __init__(self, service: Resource, source_dict: dict):
        self._service = service
        self._dict = source_dict
        super().__init__(service, source_dict)

    def events(self, max_results = 2000) -> list:
        '''Gets all events in the calendar'''
        events_resp = self._service.events().list(calendarId = self.id, maxResults = max_results).execute()
        return [Event(self, event_dict) for event_dict in events_resp['items']]

    def event(self, event_id: str) -> Event:
        event_dict = self._service.events().get(calendarId = self.id, eventId = event_id).execute()
        return Event(self, event_dict)

    def add(self, body: dict) -> Event:
        event_dict = self._service.events().insert(calendarId = self.id, body = body).execute()
        return Event(self, event_dict)

    def _update(self):
        self._dict = self._service.calendars().get(calendarId = self.id).execute()