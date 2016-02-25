# [译]修复 Android 中的内存泄露—— OutOfMemoryError

在 Android 中内存泄露很容易发生。就算是可靠的程序员每天也可能在不知不觉中制造几处内存泄露。你也许不会发现它们甚至不知道它们的存在。直到你遇到这样的异常...

```
java.lang.OutOfMemoryError: Failed to allocate a 4308492 byte allocation with 467872 free bytes and 456KB until OOM
at dalvik.system.VMRuntime.newNonMovableArray(Native Method)
at android.graphics.BitmapFactory.nativeDecodeAsset(Native Method)
at android.graphics.BitmapFactory.decodeStream(BitmapFactory.java:609)
at android.graphics.BitmapFactory.decodeResourceStream(BitmapFactory.java:444)
at android.graphics.drawable.Drawable.createFromResourceStream(Drawable.java:988)
at android.content.res.Resources.loadDrawableForCookie(Resources.java:2580)
at android.content.res.Resources.loadDrawable(Resources.java:2487)
at android.content.res.Resources.getDrawable(Resources.java:814)
at android.content.res.Resources.getDrawable(Resources.java:767)
at com.nostra13.universalimageloader.core.DisplayImageOptions.getImageOnLoading(DisplayImageOptions.java:134)
```

我去！这是什么鬼？这是不是意味着我的位图太大了？

不幸的是，这种堆栈跟踪信息可能有一点欺骗性。一般而言，当你得到 OutOfMemoryError 时，十有八九是遇到了内存泄露。第一次遇到此类堆栈跟踪信息令我感到困惑，并以为是位图太大导致的，但我错了。

## 什么是内存泄露？

> 指在程序中释放无效内存失败的情况，导致性能下降或出错。


## Android 中的内存泄露是如何产生的？

在 Android 中内存泄露真的很容易产生，这可能是问题的一部分。最大的问题在于 Android [Context](http://developer.android.com/reference/android/content/Context.html) 对象。

每个应用都有一个全局应用上下文环境（`getApplicationContext()`）。每个活动都是 `Context` 的一个子类。一般而言，内存泄露会与一个活动泄露相关联。

谦逊的开发者会在需要的线程中传入上下文对象。你认为使一些静态的 TextView 持有活动的引用有效吗？

\*讽刺的是，不要在家中尝试此类事情\*

![]()
> 事情运作的对立面

像在 Android [内存监视器](http://developer.android.com/tools/performance/memory-monitor/index.html) 中描述的那样，持续增长的内存占用是内存泄露的一个很大的警告信号。

![]()
> 监控有内存泄露的 Android 内存监视器


![]()
> 解决内存泄露后的 Android 内存监视器

如你所见，在第一张图中，应用不能回收已使用过的内存。直到内存占用达到 300MB 后的某个点，发生了 OutOfMemoryError。第二张图展示了应用可以回收无效内存占用，保持了内存使用的平衡状态。

## 如何避免内存泄露？

+ 避免在活动和碎片以外传入上下文对象。
+ **永远不要**使用静态变量创建/存储上下文或视图。这是内存泄露的首要信号。

	```java
	private static TextView textView; //DO NOT DO THIS
	private static Context context; //DO NOT DO THIS
	```
+ 始终记着在 onPause()/onDestroy()方法中解除注册监听器，例如定位服务，显示管理服务和自定义监听器等。
+ 不要在 AsyncTask 或者 后台线程中持有视图的强引用。视图可能会被关闭，AsyncTask 会持续执行并一直持有该视图的引用。
+ 如果可以，尽量使用应用上下文对象（getApplicationContext()）代替视图上下文。
+ 尽量不要使用非静态内部类。在非静态内部类中存储活动或视图的引用会导致内存泄露。如果需要，请使用[WeakReference](http://developer.android.com/reference/java/lang/ref/WeakReference.html)。

## 如何修复内存泄露？

修复内存泄露需要一些实践、多次试错，而且会遇到很多错误。内存泄露很难跟踪。幸运的是有一些工具可以帮助我们







