#!/usr/bin/env   python
# -*- encoding:  utf-8 -*-
#
#       Author:  Rex Zhang
#  Create Time:  2012-10-01 19:38
#    File name:  utils.py

def set_timezone(zone='Asia/Shanghai'):
    import os
    import time
    os.environ['TZ'] = zone
    time.tzset()
