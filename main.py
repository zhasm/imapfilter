#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-09-29 18:26
#    File name:  main.py

from rule import RuleManager
from msg import Msg
from pprint import pprint
from tornado.options import parse_command_line
import sys
import logging

parse_command_line()

ruleman = RuleManager()
ruleman.load_cfs()

pprint(ruleman.rules, indent=4)

for f in sys.argv[1:]:
    msg = Msg(file=f)
    rule = 'from_jp_to_dot_com'
    result = ruleman.if_match(msg, rule)
    if result:
        print 'msg %s is fired by %s' % (f, rule)
