from pathlib import Path
from json import dump
from os import system, chdir

chdir(Path(__file__).parent) # Assicura che il programma possa accedere agli altri file nella cartella

print('[i] Installing required packages...')
system("pip install -r requirements.txt")
print()

from src.google_calendar import API_SCOPES
from src.calendar_adder import ADDED_EVENTS_PATH
from src.google_api import GoogleAPI
from src.mastercom import get_token
from main import CALENDAR_ID_PATH, GOOGLE_TOKEN_PATH, GOOGLE_CREDS_PATH, MASTERCOM_TOKEN_PATH, MASTERCOM_URL_ID, MASTERCOM_SCHOOL_ID, MASTERCOM_STUDENT_ID


if __name__ == '__main__':
    chdir(Path(__file__).parent) # Assicura che il programma possa accedere agli altri file nella cartella

    # Setup per il registro elettronico
    print('[i] Username e password non verranno salvati')

    while True:
        username = input('Inserire username del registro: ')
        password = input('Inserire password del registro: ')

        try:
            token = get_token(username, password, MASTERCOM_URL_ID, MASTERCOM_SCHOOL_ID)
        except ValueError:
            print('[!] Username o password errata')
        else:
            break

    data_dict = {
        'token': token,
        'mastercom_id': MASTERCOM_URL_ID,
        'school_id': MASTERCOM_SCHOOL_ID,
        'student_id': MASTERCOM_STUDENT_ID,
    }

    with open(MASTERCOM_TOKEN_PATH, 'w+') as file:
        dump(data_dict, file, indent=True)

    # Setup per Google Calendar
    GoogleAPI.generate_token(API_SCOPES, GOOGLE_TOKEN_PATH, GOOGLE_CREDS_PATH)

    calendar_id = input("Inserire l'ID del calendario: ")
    with open(CALENDAR_ID_PATH, 'w+') as file: # Salva l'ID in un file
        dump({'calendar_id': calendar_id}, file)

    if not ADDED_EVENTS_PATH.exists():
        with open(ADDED_EVENTS_PATH, 'w+') as file:
            dump({}, file)

    input('\n[i] Setup concluso, premere invio per chiudere la finestra') # Per evitare che si chiuda la finestra
