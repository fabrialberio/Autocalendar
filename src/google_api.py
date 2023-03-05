# -*- coding: utf8 -*-
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from google.oauth2.credentials import Credentials


@dataclass
class GoogleAPI:
    credentials: Credentials

    @classmethod
    def generate_token(cls,
            scopes: list,
            token_path: Path,
            creds_path: Path) -> 'GoogleAPI':
        '''Generates a new token file and returns a GoogleAPI object using it'''
        if not creds_path.exists():
            raise FileExistsError('No credentials found. Follow this guide https://developers.google.com/workspace/guides/create-credentials and paste them in \'credentials/credentials.json\'')

        if token_path.exists():
            return GoogleAPI.from_token(token_path)
        else:
            creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
                creds = flow.run_local_server(port=0)

            with open(token_path, 'w+') as token_file:
                token_file.write(creds.to_json())

        return GoogleAPI(creds)

    @classmethod
    def from_token(cls, token_path: Path) -> 'GoogleAPI':
        '''Creates a GoogleAPI object from a token file'''
        creds = Credentials.from_authorized_user_file(token_path)
        return GoogleAPI(creds)

    def build(self, service_name: str, version: str) -> Resource:
        '''Returns a Resource object given the service name and version'''
        return build(service_name, version, credentials=self.credentials)


@dataclass(init=False)
class GoogleAPIObject(Protocol):
    '''An abstraction of dictionary-based Google API objects'''
    _service: Resource
    _dict: dict

    @classmethod
    def from_id(cls, service: Resource, id: str):
        '''Creates and updates an object by constructing an empty dict from the id'''
        obj = cls(service, {'id': id})
        obj._update()
        return obj

    def __init__(self, service: Resource, source_dict: dict) -> None:
        self._service = service
        self._dict = source_dict

    def _update(self):
        '''
        Updates the _dict property

        Should be called after anything that influences the object server-side.
        '''
        ...

    def __iter__(self):
        return iter(self._dict.items())

    def __getattr__(self, name: str):
        if name in self.__annotations__.keys():
            return self._dict.get(name)
        else:
            raise AttributeError(f'{self} has no attribute "{name}"')