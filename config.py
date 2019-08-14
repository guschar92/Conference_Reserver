import os

basedir = os.path.abspath(os.path.dirname(__file__))

POSTGRES2 = {
    'host': 'dbhost',
    'port': '5432',
    'user': 'dbuser',
    'pw': 'dbpass',
    'db': 'db'
}

class Conf:
    MAIL_DEFAULT_SENDER = 'mail@sender.com'  # '"KTHMA.gr" <noreply@kthma.gr>'
    MAIL_SERVER = "mail.server"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'mail@sender.com'
    MAIL_PASSWORD = 'mail_pass'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    DEBUG = True
    SECRET_KEY = os.urandom(12)
    SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES2
    PSYCOPG_URI2 = 'host=%(host)s port=%(port)s dbname=%(db)s user=%(user)s password=%(pw)s' % POSTGRES2


