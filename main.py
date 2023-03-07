from pathlib import Path
from json import load
from os import chdir

from src.calendar_adder import CalendarAdder, AssignmentType


# Percorsi dei file necessari al programma
MASTERCOM_TOKEN_PATH = Path('config/mastercom_token.json')
GOOGLE_TOKEN_PATH = Path('config/google_token.json')
GOOGLE_CREDS_PATH = Path('config/google_credentials.json')
CALENDAR_ID_PATH = Path('config/calendar_id.json')

# Dati per l'accesso al registro
MASTERCOM_URL_ID = 'giovio-co-sito'
MASTERCOM_SCHOOL_ID = 'giovio-co'
MASTERCOM_STUDENT_ID = 1005465


# Funzione main
if __name__ == '__main__':
    chdir(Path(__file__).parent) # Assicura che il programma possa accedere agli altri file nella cartella

    if not MASTERCOM_TOKEN_PATH.exists() or not GOOGLE_TOKEN_PATH.exists():
        print('[i] Required files not found, make shure you run setup.py before this file')
        exit()
    
    # Recupera dal file l'ID del calendario
    with open(CALENDAR_ID_PATH, 'r') as file:
        calendar_id = load(file)['calendar_id']

    # Utilizza CalendarAdder
    calendar_adder = CalendarAdder.from_tokens(MASTERCOM_TOKEN_PATH, GOOGLE_TOKEN_PATH, calendar_id=calendar_id) # Inizializza CalendarAdder con l'ID

    calendar_adder.add_all(AssignmentType.HOMEWORK) # Aggiunge al calendario i compiti (tipo HOMEWORK)
    calendar_adder.add_all(AssignmentType.TEST) # Aggiunge al calendario le verifiche (tipo TEST)
    calendar_adder.print_tally() # Stampa un riassunto delle operazioni eseguite

    input('\nPremere invio per chiudere la finestra') # Aspetta l'input dell'utente prima di chiudere la finestra
