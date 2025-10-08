import json
import os

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate

from src.constants import DATA_FOLDER_NAME, DATABASE_FILENAME
from src.db_session import init_db

from ..data_manager.models import db
from ..scheduler.scheduler import start_scheduler


def load_localizations():
    """
    Loads localization data from language (EN, FR & DE) JSON files into
    a dictionary.

    Returns:
    dict: A dictionary where keys are language codes, and values are the parsed
    JSON content.
    """
    locales_dir = os.path.join(os.path.dirname(__file__), '..', 'locales')
    localizations = {}
    for filename in os.listdir(locales_dir):
        if filename.endswith('.json'):
            lang = filename.split('.')[0]
            with open(os.path.join(locales_dir, filename), 'r', encoding='utf-8') as f:
                localizations[lang] = json.load(f)
    return localizations


def setup_scheduler(app):
    """
    Initializes and starts the scheduler within the application.
    Args:
        app (Flask): The Flask application instance.
    """
    with app.app_context():
        start_scheduler(app)


def configure_db(app):
    """
    Configures and initializes the SQLite Database for the Flask application
    
    Args:
        app(Flask) The flask application instance for which a database needs to be configured.
    """
    # Resolves the database directory and ensures it exists
    base_directory = os.path.abspath(os.path.dirname(__file__))
    project_directory = os.path.join(base_directory, '..', '..')
    database_directory = os.path.join(project_directory, DATA_FOLDER_NAME)

    database_directory = os.path.normpath(database_directory)
    if not os.path.exists(database_directory):
        os.makedirs(database_directory)

    # Building the db URI + updating the Flask app config
    database_path = os.path.join(database_directory, DATABASE_FILENAME)
    db_uri = 'sqlite:///' + database_path
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initializing the SQLAlchemy extension with the app
    db.init_app(app)

    # Creating the db within the app's context + setup of the db
    with app.app_context():
        print("Creating database tables")
        db.create_all()
        print("Tables created successfully")
    init_db(db_uri)


def create_app():
    """
    Creates and configures the Flask application instance.
    
    Returns:
        app(Flask) : The configured Flask application instance.
    """
    # Loading environment variables from a `.env` file.
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    env_path = os.path.join(base_dir, '.env')
    load_dotenv(dotenv_path=env_path, override=True)

    # Creating a Flask app instance with application context preservation
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../../templates'),
                static_folder=os.path.join(os.path.dirname(__file__), '../../static'))
    
    # Ensure the application context is preserved
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = True

    # Loading localization data
    app.extensions['localizations'] = load_localizations()
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

    # Configuring the database for the app
    configure_db(app)
    migrate = Migrate(app, db)

    # Set up scheduler after all app configuration is done
    setup_scheduler(app)

    return app