from src.communication.conversation_starter import start_conversations
from src.data_manager.form_data_manager import fill_db_from_google_form_data


def init_experiment(): #TODO : Integrate in the routes and prevent from running two times in one app running session.
    fill_db_from_google_form_data()
    start_conversations()
