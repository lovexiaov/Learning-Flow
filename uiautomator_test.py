# -*- coding: utf-8 -*-

"""
test for uiautomator, a python wrapper of android Uiautomator
"""

from uiautomator import device as d
import os
import time
import sys
reload(sys)
sys.setdefaultencoding('utf8')

def sendevent(event) :
    os.popen('adb shell sendevent %s' %event)

# d.screen.off()
# print(d.info)
# if d.screen == "off":
#     d.screen.on()
#     time.sleep(2)
#     if d(resourceId='com.android.systemui:id/lock_icon').exists:
#         d.swipe(800, 1000, 800, 300, steps=10)
#         time.sleep(2)
# d.press('back')
# d.click(65, 1158) # does not work, need long_click
# 打开左下角菜单
# d.long_click(65, 1158)
# d(text='计算器').click()
# time.sleep(2)
# open fullscreen titlebar
# os.popen('adb shell am broadcast -a com.lenovo.multiwindow.FULLSCREEN_SHOW_TITLEBAR')
# close btn
# d.click(1861, 51)
# window btn
# d.click(1762, 45)
# minimum btn
# d.click(1662, 45)
os.popen('monkeyrunner sendevent.py')
# os.popen('monkeyrunner monkeyrunner_wrapper.py')