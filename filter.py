#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-09-29 21:34
#    File name:  filter.py

from rule import RuleManager, RuleBase
import logging
import json

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

    def _core_reg(self, rule_type, name, rule):
        white_spaces = self.white_spaces
        kw = {}
        kw[self.type_str] = rule_type
        kw['rule_name'] = kw['name'] = name
        kw['dest'] = rule

        self.register(**kw)

    def test_match_and_take_action(self, imap, msgs):
        'msgs is list of {id, msg} dicts'

        matched = []
        for (mid, msg) in msgs:
            subject = msg.get_header('subject')
            for rule in self.rules.values():
                if mid not in matched and self.ruleman.is_match(msg, rule.rule_name):
                    logging.warning('rule %s is matching msg: %s' %\
                                    (rule.name, subject))
                    try:
                        ret = rule.do(imap, mid)
                        logging.info(ret)
                        break
                    except Exception as e:
                        logging.error(e)

            mark_as_unread(imap, mid)
