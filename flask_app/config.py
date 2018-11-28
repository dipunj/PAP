import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    UPLOAD_FOLDER                  = os.path.join(basedir, 'db/')
    SQLALCHEMY_DATABASE_URI        = "sqlite:///{}".format(os.path.join(UPLOAD_FOLDER, "users.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False