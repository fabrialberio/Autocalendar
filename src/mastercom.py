from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from html import unescape
from json import loads
from enum import Enum

from requests import get, post

# Workaround for platforms that do not natively support fromisoformat()
try:
    datetime.fromisoformat(datetime.now().isoformat())
except AttributeError:
    from backports.datetime_fromisoformat import MonkeyPatch
    MonkeyPatch.patch_fromisoformat()


class AssignmentType(Enum):
    TEST = 'test'
    HOMEWORK = 'homework'
    TIMETABLE = 'timetable'

SUBJECT_NAME_MAP = {
    # Subject ID: Subject name
    1000114: 'Italiano',
    1000117: 'Matematica',
    1000118: 'Fisica',
    1000119: 'Scienze',
    1000121: 'Filosofia',
    1000123: 'Motoria',
    1000124: 'Religione',
    1000130: 'Storia',
    1000132: 'Inglese',
    1000133: 'Informatica',
    1000134: 'Arte'}

REQUEST_MAP = {
    # Request type: Request url
    AssignmentType.TEST: 'agenda_plain',
    AssignmentType.HOMEWORK: 'compiti_plain',
    AssignmentType.TIMETABLE: 'orario_plain'}

BASE_URL = 'https://{}.registroelettronico.com/api/v{}'


def get_token(
        username: str,
        password: str,
        mastercom_id: str,
        school_id: str,
    ) -> str:
    login_url = BASE_URL.format(mastercom_id, 4) + '/utenti/login/'

    payload = {
        'utente': username,
        'password': password,
        'mastercom': school_id}

    response = post(login_url, json=payload)

    if response.status_code == 200:
        return loads(response.text)['token']
    if response.status_code == 401:
        raise ValueError('Username or password is incorrect')
    else:
        raise ConnectionError(f'Request failed with status code {response.status_code}')



@dataclass
class Assignment:
    start: datetime
    kind: AssignmentType
    unique_id: str = None

    subject_id: int = None
    end: datetime = None
    title: str = None
    description: str = None

    def __post_init__(self) -> None:
        seed = self.start.isoformat() + self.kind.name
        self.unique_id = sha256(seed.encode('utf8')).hexdigest()

    @property
    def subject(self) -> str:
        return SUBJECT_NAME_MAP.get(self.subject_id, '')


@dataclass(init=False)
class MastercomAPI:
    token: str
    url: str

    @classmethod
    def from_user_pass(cls,
            username: str,
            password: str,
            mastercom_id: str,
            school_id: str,
            student_id: str,
            school_year: int = None,
        ) -> 'MastercomAPI':
        token = get_token(username, password, mastercom_id, school_id)
        return MastercomAPI(token, mastercom_id, school_id, student_id, school_year)

    def __init__(self,
            token: str,
            mastercom_id: str,
            school_id: str,
            student_id: str,
            school_year: int = None,
        ) -> None:

        if school_year == None:
            school_year = (datetime.now() - timedelta(days=365/2)).year

        self.url = BASE_URL.format(mastercom_id, 3) + f'/scuole/{school_id}/studenti/{student_id}/{school_year}_{school_year + 1}'
        self.token = token

    def request(self, 
            request_type: AssignmentType, 
            start: datetime = None, 
            end: datetime = None, 
            params: dict = {}
        ) -> list:
        headers = {'Authorization': f'JWT {self.token}'}

        params.update({
            'data_inizio': start.date().isoformat() if start != None else None,
            'data_fine': end.date().isoformat() if end != None else None})

        response = get(f'{self.url}/{REQUEST_MAP[request_type]}', headers=headers, params=params)

        if response.status_code != 200:
            raise ConnectionError(f'Request failed with status code {response.status_code}')

        response_list = loads(response.text)
        response_list = [{k: (unescape(v) if type(v) == str else v) for k, v in d.items()} for d in response_list]

        return response_list

    def homework(self, start: datetime = None, end: datetime = None) -> list:
        raw_homework = self.request(AssignmentType.HOMEWORK, start, end)

        return [Assignment(
            start = datetime.fromisoformat(i['data'][:19]),
            kind = AssignmentType.HOMEWORK,
            subject_id = int(i['id_materia'] or 0),
            description = i['titolo'],
        ) for i in raw_homework]

    def tests(self, start: datetime = None, end: datetime = None) -> list:
        raw_tests = self.request(AssignmentType.TEST, start, end)

        return [Assignment(
            start = datetime.fromisoformat(i['data'][:19]),
            kind = AssignmentType.TEST,
            title = i['sottotitolo'],
            description = i['titolo'],
        ) for i in raw_tests]

    def timetable(self, start: datetime, interval: timedelta = timedelta(days=6)) -> list:
        raw_timetable = self.request(AssignmentType.TIMETABLE, start, start + interval)

        return [Assignment(
            start = datetime.fromisoformat(i['data_ora_inizio']),
            end = datetime.fromisoformat(i['data_ora_fine']),
            kind = AssignmentType.TIMETABLE,
            subject_id = int(i['id_materia'] or 0),
        ) for i in raw_timetable]