#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-09-30 16:13
#    File name:  imap.py

from imapclient import IMAPClient
from settings import HOST, USERNAME, PASSWORD, ssl
from settings import debug, imap_acct, default_not_matched_dest
from msg import Msg
from time import sleep
from threading import Thread

from tornado.options import parse_command_line

from rule import RuleManager
from filter import FilterManager
import logging


class IMAP(Thread):
    def __init__(self, filman):
        super(IMAP, self).__init__()
        self.imap = IMAPClient(HOST, use_uid=True, ssl=ssl)
        self.imap.login(USERNAME, PASSWORD)
        self.messages = []
        self.filterman = filman
        self.counter = 0
        self.check_dests()

        self.loop()

    def check_dests(self):
        dests = self.filterman.get_dests()
        for d in dests:
            if not self.imap.folder_exists(d):
                self.imap.create_folder(d)
                logging.info('[create folder] %s' % d)

        if not self.imap.folder_exists(default_not_matched_dest):
            self.imap.create_folder(default_not_matched_dest)
            logging.info('[create folder] %s' % default_not_matched_dest)

    def mark_as_unread(self, msg):
        return self.imap.remove_flags(msgs, ('\\SEEN'))

    def check(self):
        server = self.imap
        select_info = server.select_folder('INBOX')
        logging.info("source imap inited: %r" % select_info)
        messages = server.search(['NOT SEEN'])
        messages = sorted(messages, reverse=True)
        self.messages = list(messages)
        logging.info('got %d unread messages' % len(self.messages))

    def idle(self, secs=30):
        server = self.imap
        server.idle()
        responses = server.idle_check(timeout=secs)
        text, responses = server.idle_done()
        logging.info('idle response: %s' % (responses))
        return not responses

    def loop(self):
        server = self.imap
        logging.info('enter loop %d' % self.counter)
        self.counter += 1
        self.check()

        while self.messages:
            self._dozen()

        self.imap.close_folder()

    def _dozen(self):
        if self.messages:
            msgs = self.messages[:12]
            self.messages = self.messages[12:]
        else:
            return
        logging.info('processing the first %d msgs; left %d...' % (len(msgs), len(self.messages)))
        logging.info(msgs)
        response = self.imap.fetch(msgs, ['RFC822'])
        msgs = [(msgid, Msg(string=data['RFC822']))
                for (msgid, data) in response.iteritems()]

        self.filterman.test_match_and_take_action(self.imap, msgs)

    def run(self):
        count = 0
        while True:
            count += 1
            logging.info('idle counter: %d' % count)
            self.idle() or self.loop()
#            self.imap.noop() or self.loop()
            sleep(10)
            if not count % 5:  # do loop every 10 runs.
                self.loop()


def set_timezone(zone='Asia/Shanghai'):
    import os
    import time
    os.environ['TZ'] = zone
    time.tzset()

if __name__ == '__main__':
    set_timezone()
    parse_command_line()

    ruleman = RuleManager()
    ruleman.load_cfs()
    filman = FilterManager(ruleman=ruleman)
    i = IMAP(filman=filman)

    i.start()
    i.join()
