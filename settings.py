HOST = ''
USERNAME = ''
PASSWORD = ''
ssl = True

smtp_host = 'smtp.gmail.com'
smtp_port = 587
smtp_pwd = ''
from_addr = to_addr = ''

imap_acct = {
    'host': 'imap.gmail.com',
    'user': '',
    'pwd': '',
}

debug = None

#actual parameters can be in 'local_settings' if exists
#useful for local testing.
try:
    from local_settings import *
except ImportError:
    pass
