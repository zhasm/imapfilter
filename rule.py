#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-09-29 11:47
#    File name:  header.py

import logging
import re
import json
from msg import Msg

ruleman = None

class ReservedKeywords(object):
    def __init__(self):
        self.rk= {
            'and': '&&',
            'or': '||',
            'not': '!',
            }
    def escape(self, p):
        'convert keyword to symbol'
        regex = re.compile(r'(?i)\b(%s)\b' % ('|'.join(self.rk.keys())))

        def _rep(match_obj):
            match = match_obj.group(1)
            return self.rk[match]
        return regex.sub(_rep, p)

    def unescape(self, p):
        'convert symbol to reserved keyword'
        return p.replace('&&', ' and ').replace('||', ' or ').replace('!', ' not ').replace('  ', ' ')

class RuleBase(object):

    def get_fields(self):
        return NotImplemented

    def _rule_name_validator(self, name):
        'not in the reserved words; length >=3; regex =~ /^\w+_\w+$/ '
        reserved_words = ['and', 'or', 'not']
        if name.lower() in reserved_words:
            return False
        if len(name) < 3:
            return False
        regex = re.compile(r'^\w+_\w+$')
        return True if regex.search(name) else False

    def __init__(self, **kwargs):
        'rule name check: \w+'
        name = kwargs.get('name')
        if not self._rule_name_validator(name):
            logging.error('rule name %s is not valid!' % name)
            return

        for k in self.get_fields():
            setattr(self, k, kwargs.get(k))

    def if_match(self, msg):
        return NotImplemented

    def __repr__(self):
        ret = {}
        for k in self.get_fields():
            v = str(getattr(self, k))
            ret[k] = v
        return json.dumps(ret)

class Header(RuleBase):

    def __init__(self, **kwargs):
        super(Header, self).__init__(**kwargs)
        self.regex = re.compile(self.regex)

    def get_fields(self):
        return ['name', 'header_name', 'regex', 'rule_type']

    def if_match(self, msg):
        header = msg.get_header(self.header_name)
        if header:
            for i in header:
                if self.regex.search(i):
                    return True
        return False

class Meta(RuleBase):

    def __init__(self, **kwargs):
        super(Meta, self).__init__(**kwargs)

    def get_fields(self):
        return ['name', 'expr', 'rule_type']

    def gen_rule(self, msg):

        rk = ReservedKeywords()
        expr = rk.escape(self.expr)
        regex = re.compile(r'\b(\w+_\w+\b)')
        expr = regex.sub(r'''%(ruleman)s.get_rule("\1").if_match(%(msg)s)''', expr)
        expr = rk.unescape(expr)

        return expr

    def if_match(self, msg):
        return self.gen_rule(msg)

class RuleManager(object):

    def __init__(self):
        self.rules = {}

    def register(self, **kwargs):
        mapper = {
            'header': Header,
            'meta': Meta,
            }
        name = kwargs.get('name')
        if self.get_rule(name):
            logging.error('dup Rule: %s' % name)
            return
        rule_type = kwargs.get('rule_type')
        rule = mapper[rule_type](**kwargs)
        self.rules[name] = rule
        return True

    def load_one_cf(self, fn):
        lines = open(fn, 'r').readlines()
        white_spaces = re.compile(r'\s+')
        if not lines:
            return

        def _trim(line):
            if line:
                line = line.strip()
                if line:
                    if not line.startswith('#'):
                        return line

        #there might be empty line within
        lines = (_trim(i) for i in lines)
        for i in lines:
            if not i:
                continue
            kw = {}
            rule_type, name, rule = white_spaces.split(i, 2)
            rule_type = rule_type.lower()
            kw['rule_type'] = rule_type
            kw['name'] = name

            if rule_type == 'header':
                h, r = white_spaces.split(rule, 1)
                kw['header_name'] = h
                kw['regex'] = r
            elif rule_type == 'meta':
                kw['expr'] = rule

            self.register(**kw)

    def load_cfs(self, path=None):
        from glob import glob
        if not path:
            path='./conf'
        filenames = glob('%s/*.cf' % path)
        for fn in filenames:
            self.load_one_cf(fn)

    def get_rule(self, name):
        return self.rules.get(name, None)

    def if_match(self, msg, rule_name):
        rule = self.get_rule(rule_name)
        if rule.rule_type == 'header':
            return rule.if_match(msg)
        else:
            template = rule.if_match(msg)
            raw = template % ({
                'ruleman': 'self',
                'msg': 'msg',
                })
            try:
                return eval(raw)
            except Exception as e:
                print raw, e
