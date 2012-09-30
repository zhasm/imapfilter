#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-09-29 21:34
#    File name:  filter.py

from rule import RuleManager, RuleBase
import logging


class ActionBase(RuleBase):
    '''{
        'name': action_name,
        'rule': ruleman.get_rule(rule_name),
        'action_type': one of 'copy, delete, move'
        'desc': dest, #for copy and move
        }'''
    def get_fields(self):
        return ['name', 'rule_name', 'action_type', 'desc']

    def is_match(self, msg):
        return self.rule.is_match(msg)

    def do(self):
        return NotImplemented


class Copy(ActionBase):
    'msg here is msg id'
    def do(self, imap, msgs):
        return imap.copy(msgs, self.desc)


class Delete(ActionBase):

    def do(self, imap, msgs):
        ret = []
        ret.append(imap.delete_messages(msgs))
        ret.append(imap.expunge())
        return ' '.join(ret)


class Move(ActionBase):

    def do(self, imap, msgs):
        ret = []
        ret.append(imap.copy(msgs, self.desc))
        ret.append(imap.delete_messages(msgs))
        ret.append(imap.expunge())
        return ' '.join(ret)


class FilterManager(RuleManager):

    def __init__(self, ruleman, path=None):
        try:
            super(FilterManager, self).__init__()
        except Exception as e:
            logging.error(e)

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
        kw['name'] = name

        rule_name, dest = self.white_spaces.split(rule + ' Trash', 1)
        print 'rulename, dest:', rule_name, dest
        kw['rule'] = self.ruleman.get_rule(rule_name)
        kw['dest'] = dest

        self.register(**kw)

    def test_match_and_take_action(self, imap, msgs):
        'msgs is list of {id, msg} dicts'

        for mid, msg in msgs.iteritems():
            for rule in self.rules.values():
                if rule.is_match(msg):
                    try:
                        ret = rule.do(mid)
                        logging.info(ret)
                    except Exception as e:
                        logging.error(e)
