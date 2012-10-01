#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-09-29 16:08
#    File name:  msg.py

import email
from email import Header
from email.Iterators import typed_subpart_iterator
from email.iterators import _structure
import logging
import re


class Msg(object):

    def __init__(self, **kwargs):
        '''kwargs = {
                'file': 'filename with fullpath',
                or
                'string': 'string that contains the msg'
        }'''
        self.msg = None
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
            # logging.info('got email from string')
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
            return '\n'.join((self._trim_line(h) for h in headers))
        else:
            return ""

    def _get_headers(self, *headers):
        return '\n'.join((self.get_header(i) for i in headers))

    def get_to_all(self):
        return self._get_headers(*('to', 'cc'))

    def get_involved(self):
        return self._get_headers(*('from', 'to', 'cc'))

    def get_all_headers(self, with_header_name=False):

        headers = ['subject', 'from', 'to', 'message-id']
        if not with_header_name:
            return '\n'.join([self.get_header(h) for h in headers])
        else:
            return '\n'.join(['%s: %s' %(h.title(), self.get_header(h)) for h in headers])

    def get_content_type(self, msg=None):
        if not msg:
            msg = self.msg
        ret = []
        ret.append(msg.get_content_type())

        if msg.is_multipart():
            for subpart in msg.get_payload():
                ret.append(self.get_content_type(subpart))

        return ret

    def get_body(self, format=""):
        'when the body is of multipart, the `format` is applicable.'
        'format = plain, text only'
        'format = html, html only'
        'if no format specified, return both.'

        def _decode_msg(msg):
            'decode one part of a msg'
            if msg:
                return unicode(
                    msg.get_payload(decode=True),
                    msg.get_content_charset() or 'utf-8',
                    'replace'
                ).strip().encode('utf-8')
            else:
                return ""

        if self.msg.is_multipart():
            parts = typed_subpart_iterator(self.msg, 'text')
            if parts:
                return '\n'.join([_decode_msg(p) for p in parts])
            return ""

        else:
            body = unicode(self.msg.get_payload(decode=True),
                           self.msg.get_content_charset() or 'utf-8', "replace")
            return body.strip().encode('utf-8')

    def get_body_len(self):
        return len(self.get_body())

    def get_stucture(self):
        'print to stdout.'
        _structure(self.msg)

    def has_image(self, msg=None):
        ret = str(self.get_content_type())
        return True if ret.count('image/') else False


if __name__ == '__main__':
    import sys
    for i in sys.argv[1:]:
        print i
        msg = Msg(file=i)
        msg.get_stucture()
        print msg.get_content_type()
        print 'any images?', msg.has_image(), msg.get_content_type()
        print 'involved', msg.get_involved()
        print 'to_all', msg.get_to_all()
