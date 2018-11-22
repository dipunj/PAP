import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    UPLOAD_FOLDER                  = os.path.join(basedir, 'db/')
    SQLALCHEMY_DATABASE_URI        = "sqlite:///{}".format(os.path.join(UPLOAD_FOLDER, "users.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False