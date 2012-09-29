#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-09-29 16:08
#    File name:  msg.py

import email
from email import Header
import logging
import re

class Msg(object):

    def __init__(self, **kwargs):
        '''kwargs = {
                'file': 'filename with fullpath',
                or
                'string': 'string that contains the msg'
        }'''
        self.msg=None
        if 'file' in kwargs:
            try:
                f = kwargs.get('file')
                handle = open(f, 'r')
                self.msg = email.message_from_file(handle)
            except Exception as e:
                logging.error(e)
        elif 'string'in kwargs:
            string = kwargs.get('string')
            self.msg = email.message_from_string(string)
            logging.info('got email from string')
        else:
            logging.error('can not parse email from either string or file.')

    def x_header(self, h):

        reobj = re.compile(r"=\?[^?]+\?[bq]\?[^?]+\?=", re.IGNORECASE)
        result = reobj.search(h)

        def computereplacement(matchobj):
            text, coding = Header.decode_header(matchobj.group(0))[0]
            try:
                return text.strip().decode(coding).encode('utf-8')
            except Exception as e:
                return text

        if result:
            return reobj.sub(computereplacement, h)
        else:
            return h

    def _trim_line(self, line):
        trim = re.compile(r'[ \t]+')
        line = line.replace('\n', ' ')
        line = trim.sub(' ', line)
        line = self.x_header(line)
        return line

    def get_header(self, header_name):
        'return all the headers of the given name'
        headers = self.msg.get_all(header_name)

        if headers:
            return (self._trim_line(h) for h in headers)
        else:
            return ""
