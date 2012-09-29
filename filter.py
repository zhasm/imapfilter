#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-09-29 21:34
#    File name:  filter.py

from rule import Header, Meta, RuleManager

class Filter(object):
    def __init__(self, ruleman):
        self.ruleman = ruleman


