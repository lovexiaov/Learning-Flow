# -*- coding: utf-8 -*-
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
# 用来录制脚本的类
from com.android.monkeyrunner.recorder import MonkeyRecorder as recorder
import os

# helperContent = MonkeyRunner.help('html')
#
# helperfile = open('monkeyrunner_helper.html', w)
# helperfile.write(helperContent)
# helperfile.close()

result = os.popen('adb devices').readlines()

for l in result:
	if l == '\n':
		result.remove(l)

deviceList = map(lambda x: x[:-1], result)[1:]

if len(deviceList) == 0:
    MonkeyRunner.alert('There is no device connected to this computer~')
else:
    index = MonkeyRunner.choice('please select a device to run test case', deviceList)
    if index == -1:
        MonkeyRunner.alert('you have choice "Cancel", this program will quit.' )
    else:
        serial_id = deviceList[index][:-6].strip()
        print(serial_id)
        #MonkeyRunner.input('message', 'hello', 'title', 'Sure', 'Cancle')

        device = MonkeyRunner.waitForConnection(deviceId=serial_id)
        recorder.start(device)
        #obj = device.shell('cd sdcard && ls')
        #print(type(obj))
        #print(str(obj))
        device.installPackage('/Users/lovexiaov/Documents/AndroidProject/VNote/app/Vnote.apk')

        package = 'io.github.lovexiaov.vnote'

        activity = 'io.github.lovexiaov.vnote.MainActivity'

        runComponent = package + '/' + activity

        device.startActivity(component = runComponent)

        device.press('KEYCODE_MENU', 'DOWN_AND_UP')

        result = device.takeSnapshot()

        result.writeToFile('shot1.png', 'png')
