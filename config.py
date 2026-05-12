import os


class Config:
    # Secret key for signing session cookies and CSRF tokens.
    # Override SECRET_KEY in your .env file before deploying.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'nsysu-library-dev-key-change-in-production')

    # Absolute path to the SQLite database file at the project root.
    DATABASE = os.path.join(os.path.dirname(__file__), 'library.db')
