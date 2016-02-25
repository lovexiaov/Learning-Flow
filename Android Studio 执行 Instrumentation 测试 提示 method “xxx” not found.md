# Android Studio 执行 Instrumentation 测试 提示 Method "xxx" not found

刚看完 **Paul Blundell** 大神的 [《Learning Android Application Testing 2en Edition》](http://shop.oreilly.com/product/9781784395339.do)，不要问我咋看完的（搞个词典，随手查词呗~~）。准备做一次总结，然后看一下 **Godfrey Nolan** 的[《Agile Android》](http://www.apress.com/9781484297001?gtmf=s)。

然而，在练习书中的例子时出现了一个令人裆下隐隐作痛的事情：执行新写的测试用例，Android Studio 提示该方法找不到：

```
junit.framework.AssertionFailedError: Method "testSayHi" not found
at android.test.InstrumentationTestCase.runTest(InstrumentationTestCase.java:165)
at android.test.ActivityInstrumentationTestCase2.runTest(ActivityInstrumentationTestCase2.java:192)
at android.test.AndroidTestRunner.runTest(AndroidTestRunner.java:191)
at android.test.AndroidTestRunner.runTest(AndroidTestRunner.java:176)
at android.test.InstrumentationTestRunner.onStart(InstrumentationTestRunner.java:555)
at android.app.Instrumentation$InstrumentationThread.run(Instrumentation.java:1853)
```

这是啥鬼呢？**Paul** 哥也没教我咋解决啊！自己折腾起来吧~~



首先分析该错误原因：

> 既然提示该方法找不到，那肯定是没有把最新的测试 APK 装到手机里面咯。

问题确定了，那么下一步该做什么呢？当然是检查 Android Studio 的配置啦：

![]()

按照上图的提示打开运行配置窗口，然后切换到 **Miscellaneous** 标签，看到了 “Skip installation if APK has not changed” 选项默认是勾选的，如图：

![]()

猜想：勾选此项后，如果不修改应用代码，测试 APK 也会跳过安装？

瞎扯！去掉勾选后还是那样~

嗯，看来要换一条思路了……

那，把应用卸掉呢？

果然，将应用从手机上卸载后，测试正常执行。

可是，如果每次执行测试都要手动卸载一次应用太麻烦了。

那咋办咧？

再换个思路呗！这次从 强大的 Gradle 入手，我们先来看一下如何通过 Gradle 命令执行测试：

```shell
./gradlew connectedAndroidTest
```

哎哎哎，这家伙在运行完测试就自动把 APK 给卸载了。这次测试可以成功执行了，也不用手动卸载 APK 了，可是，命令行运行结果不够直观啊，调试太麻烦咯。

不过，这给我们提供了一个思路：能不能让 Android Studio 在执行测试之前编译最新的测试 APK 并安装到设备中呢？

研究半天，发现了 Gradle 中有这么一个命令： `installDebugAndroidTest`。该命令正好符合我们的需求。

那么，如何将该命令整合进来呢？还得从 Android Studio 配置入手啦，再次打开配置界面，仔细研究各项配置，终于发现了新大陆：

![]()

如图所示，该选项似乎可以在测试执行前做点什么，点击 **“+”** 在弹出菜单中赫然发现了 **Run Gradle Task** 选项：

![]()

抓紧点开看一下，在弹出的对话框中，**Gradle project** 选择 ”:app“，**Task** 选择 “installDebugAndroidTest”，然后点击 **OK** 完成配置。

![]()

![]()

此时，配置页面上已经发生了变化，如下图：

![]()

这样，我们再次执行此测试用例就不会提示方法找不到的错误了。

但是，细心的你可能已经注意到了此方法的一个缺陷：需要先执行一次该测试，失败后去修改它的配置，修改完毕后再次执行该测试才会成功。这也不比卸载 APK 简单到哪里去，不符合我们的预期，但是已经离目标很近了哦！

再次打开配置页，找到左边的 **Defaults** 标签并展开，发现有一个 **Android Tests** 子标签，如图：

![]()

在这里重复上面添加 Gradle Task 的步骤，然后保存配置。

让我们再添加一个测试用例验证此方案是否可行：

```java
public void testConquer() {
    assertTrue(true);
}
```

Yes! 万事大吉啦~~

![]()

至此，问题解决完毕。 Have Fun(0_o)~


