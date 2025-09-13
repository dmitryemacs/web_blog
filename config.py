import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mysecretkey'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://dima:zxc011@localhost/blogdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
