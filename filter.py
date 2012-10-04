#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-09-29 21:34
#    File name:  filter.py

from rule import RuleManager, RuleBase
import logging
import json
from settings import default_not_matched_dest
import threading
from threading import Lock

def mark_as_unread(imap, msgs):
    return imap.remove_flags(msgs, ('\\SEEN'))

class ActionBase(RuleBase):
    '''{
        'name': action_name,
        'rule_name': rule_name,
        'action_type': one of 'copy, delete, move'
        'dest': dest, #for copy and move
        }'''
    def get_fields(self):
        return ['name', 'rule_name', 'action_type', 'dest']

    def do(self):
        return NotImplemented


class Copy(ActionBase):
    'msg here is msg id'
    def do(self, imap, msgs):

        ret = []
        ret.append(imap.copy(msgs, self.dest))
        ret.append(mark_as_unread(imap, msgs))
        return str(ret)


class Delete(ActionBase):

    def do(self, imap, msgs):

        ret = []
        ret.append(imap.delete_messages(msgs))
        ret.append(imap.expunge())
        return str(ret)


class Move(ActionBase):

    def do(self, imap, msgs):

        ret = []
        ret.append(mark_as_unread(imap, msgs))
        ret.append(imap.copy(msgs, self.dest))
        ret.append(imap.delete_messages(msgs))
        ret.append(imap.expunge())
        return str(ret)


class FilterManager(RuleManager):

    def __init__(self, ruleman, path=None):

        super(FilterManager, self).__init__()

        self.mapper = {
            'copy': Copy,
            'delete': Delete,
            'move': Move
        }

        self.type_str = 'action_type'
        self.ext = 'filter.conf'
        self.ruleman = ruleman
        self.load_cfs(path)

        #add default action
        self.default = Move(**{
            'name': '__default',
            'dest': default_not_matched_dest,
        })

    def _core_reg(self, rule_type, name, rule):
        kw = {}
        kw[self.type_str] = rule_type
        kw['rule_name'] = kw['name'] = name
        kw['dest'] = rule

        self.register(**kw)

    def get_dests(self):
        return (self.rules[i].dest for i in self.rules)

    def test_match_and_take_action(self, imap, msgs):
        'msgs is list of {id, msg} dicts'

        for (mid, msg) in msgs:
            self.process_one_msg(imap, msg, mid)

    def process_one_msg(self, imap, msg, mid):
        flag_matched = False
        subject = msg.get_header('subject')
        for rule in self.rules.values():
            if self.ruleman.is_match(msg, rule.rule_name):
                logging.warning('filter %s is matching msg: %s' %
                                (rule.name, subject))
                flag_matched = True
                try:
                    ret = rule.do(imap, mid)
                    logging.info(ret)
                    break
                except Exception as e:
                    logging.error(e)

        mark_as_unread(imap, mid)

        if not flag_matched:
            logging.error('[NOT matched by any filter]')
            logging.info('msg details:\n %s' % msg.get_all_headers(True))
            self.default.do(imap, mid)
            logging.info('msg moved to %s' % default_not_matched_dest)
