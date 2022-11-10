import os
from os import environ, path
# from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
# load_dotenv(path.join(basedir, '.env'))

FLASK_ENV = 'development'
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
# basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True
# Connect to the database

# db_user=os.getenv('DB_USER')
# db_password=os.getenv('DB_USER')
# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@localhost:5432/fyyur'
SQLALCHEMY_TRACK_MODIFICATIONS = False

