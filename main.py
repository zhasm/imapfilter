#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-09-29 18:26
#    File name:  main.py

from rule import RuleManager
from tornado.options import parse_command_line
from rule import RuleManager
from filter import FilterManager
from imap import IMAP
from utils import set_timezone


if __name__ == '__main__':
    set_timezone()
    parse_command_line()

    ruleman = RuleManager()
    ruleman.load_cfs()
    filman = FilterManager(ruleman=ruleman)
    i = IMAP(filman=filman)

    i.start()
    i.join()
