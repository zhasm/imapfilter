#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-09-29 11:47
#    File name:  header.py

import logging
import re
import json

ruleman = None


class ReservedKeywords(object):
    def __init__(self):
        self.rk = {
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
        regex = re.compile(r'^\w+[a-zA-Z]\w+$')
        return bool(regex.match(name))

    def __init__(self, **kwargs):
        'rule name check: \w+'
        name = kwargs.get('name')
        if not self._rule_name_validator(name):
            logging.error('rule name %s is not valid!' % name)
            return

        for k in self.get_fields():
            setattr(self, k, kwargs.get(k))

    def is_match(self, msg):
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
        setattr(self, 'raw_regex', self.regex)
        self.regex = re.compile(r"(?m)%s" % self.regex)

    def get_fields(self):
        return ['name', 'header_name', 'regex', 'rule_type', 'raw_regex']

    def is_match(self, msg):
        header = msg.get_header(self.header_name)
        return bool(self.regex.search(header))

class Matcher(Header):
    def get_fields(self):
        return ['name', 'header_name', 'regex', 'rule_type', 'raw_regex', 'match_func']

    def is_match(self, msg):
        func = getattr(msg, self.match_func)
        field = func()
        return bool(self.regex.search(field))


class Meta(RuleBase):

    def __init__(self, **kwargs):
        super(Meta, self).__init__(**kwargs)
        self.gen = self.gen_rule()

    def get_fields(self):
        return ['name', 'expr', 'rule_type', 'gen']

    def gen_rule(self):

        rk = ReservedKeywords()
        expr = rk.escape(self.expr)
        regex = re.compile(r'\b(\w+_\w+\b)')
        expr = regex.sub(
            r'''( %(ruleman)s.get_rule("\1").is_match(%(msg)s) )''', expr)
        expr = rk.unescape(expr)
        self.gen = expr
        return expr

    def is_match(self, msg):
        return self.gen_rule()

class Eval(Meta):

    def gen_rule(self):
        return '''%%(msg)s.%s''' % self.expr

    def is_match(self, msg):
        rule = self.gen_rule() % {'msg': 'msg'}
        result = eval(rule)
        logging.info('eval rule: %s; rule def: %s;  result: %r ' % \
                     (self.name, rule, result))
        return result

class RuleManager(object):

    def __init__(self, path=None):

        self.mapper = {
            'header': Header,
            'meta': Meta,
            'eval': Eval,
            'matcher': Matcher,
        }

        self.matcher=['to_all', 'involved', 'all_headers', 'content_type', 'body']

        self.type_str = 'rule_type'
        self.ext = '*.cf'
        self.white_spaces = re.compile(r'\s+')

    def register(self, **kwargs):
        mapper = self.mapper
        name = kwargs.get('name')
        if self.get_rule(name):
            logging.error('dup Rule: %s' % name)
            return
        rule_type = kwargs.get(self.type_str)
        rule = mapper[rule_type](**kwargs)
        self.rules[name] = rule
        return True

    def load_one_cf(self, fn):
        lines = open(fn, 'r').readlines()
        white_spaces = self.white_spaces
        all_fields = self.mapper.keys() + self.matcher
        if not lines:
            return

        def _trim(line):
            if not line: return ''
            line = line.strip()
            if not line.startswith('#'):
                return line

        lines = (_trim(i) for i in lines)

        for i in lines:
            if not i:
                continue
            try:
                rule_type, name, rule = white_spaces.split(i, 2)
            except Exception as e:
                logging.error(e)
                print i

            rule_type = rule_type.lower()
            if rule_type not in all_fields:
                continue
            self._core_reg(rule_type, name, rule)

    def _core_reg(self, rule_type, name, rule):

        kw = {}
        kw[self.type_str] = rule_type
        kw['name'] = name

        if rule_type == 'header':
            h, r = self.white_spaces.split(rule, 1)
            kw['header_name'] = h
            kw['regex'] = r
        elif rule_type in ['meta', 'eval']:
            kw['expr'] = rule
        elif rule_type in self.matcher:
            kw['rule_type'] = 'matcher'
            kw['match_func'] = 'get_%s' % rule_type
            kw['regex'] = rule

        self.register(**kw)

    def load_cfs(self, path=None):
        from glob import glob
        self.rules = {}
        if not path:
            path = './conf'
        filenames = glob('%s/%s' % (path, self.ext))
        for fn in filenames:
            self.load_one_cf(fn)

    def get_rule(self, name):
        return self.rules.get(name, None)

    def is_match(self, msg, rule_name):
        rule = self.get_rule(rule_name)

        if rule.rule_type != 'meta':
            return rule.is_match(msg)
        else:
            template = rule.is_match(msg)
            raw = template % ({
                'ruleman': 'self',
                'msg': 'msg',
            })
            try:
                result = eval(raw)
                # logging.info('meta rule %s generated: %r, result: %r' % (rule_name, raw, result))
                return bool(result)
            except Exception as e:
                logging.error(e)
                return False
