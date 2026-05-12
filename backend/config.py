import os


class Config:
    # os.environ.get() checks for an environment variable first. If one exists
    # (e.g. on a production server), it uses that. If not, it falls back to the
    # hardcoded string. This way developers don't need a .env file to run the
    # app locally, but a production deployment can set a strong secret safely.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'nsysu-library-dev-key-change-in-production')

    # __file__ is the path to this config.py file. Using it here means the
    # database is always created next to config.py (inside backend/), regardless
    # of what directory you run the server from.
    DATABASE = os.path.join(os.path.dirname(__file__), 'library.db')
