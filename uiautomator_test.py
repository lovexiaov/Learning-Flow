# -*- coding: utf-8 -*-

"""
test for uiautomator, a python wrapper of android Uiautomator
"""

from uiautomator import device as d
import os

import sys
reload(sys)
sys.setdefaultencoding('utf8')

# print(d.info)
d.screen.on()

d.press('back')

os.popen('monkeyrunner monkeyrunner_wrapper.py')