> 原文：[Mock Application in Espresso for Dependency Injection](http://blog.sqisland.com/2015/12/mock-application-in-espresso.html)
> 
> 作者：[Chiu-Ki Chan](https://www.blogger.com/profile/01970007638489793840)
> 
> 译者：[lovexiaov](http://www.jianshu.com/users/7378dce2d52c)

我看了 [Artem Zinnatullin](https://twitter.com/artem_zin) 写的[使用 Dagger，Robolectric 和 InStrumentation 在单元测试，集成测试与功能测试中模拟依赖](http://www.jianshu.com/p/d8cc1a566169)（译者注：这里将链接替换成了中译版本，文章中有原文链接）这篇好文。其中我最喜欢的部分是在测试中使用不同的 `application` 来提供不同的依赖，而我决定使用 Espresso 实现它。

## 通过自定义测试运行器模拟 application

我当前实现依赖注入（译者注：下文统一使用 DI）的方法是在我的测试 application 中暴露一个 `setComponent` 函数来提供测试组件，这样并不是太好，因为理想情况下 application 中不能包含测试指定代码。

一种新的实现方式是在 `androidTest` 文件夹中使用 application 的子类 ，并在测试时通过自定义测试运行器加载它。

```java
public class DemoApplication extends Application {
  private final DemoComponent component = createComponent();

  protected DemoComponent createComponent() {
    return DaggerDemoApplication_ApplicationComponent.builder()
        .clockModule(new ClockModule())
        .build();
  }

  public DemoComponent component() {
    return component;
  }
}
```
在此 application 中，我们使用 `createComponent()` 实例化的 `DemoComponent`，并且将它存储为 `final` 变量待以后使用。

```java
public class MockDemoApplication extends DemoApplication {
  @Override
  protected DemoComponent createComponent() {
    return DaggerMainActivityTest_TestComponent.builder()
        .mockClockModule(new MockClockModule())
        .build();
  }
}
```
测试时，我们继承自己的 application 并重写 `createComponent` 来提供测试组件。

我们需要自定义测试运行器以在测试是使用模拟 application：

```java
public class MockTestRunner extends AndroidJUnitRunner {
  @Override
  public Application newApplication(
      ClassLoader cl, String className, Context context)
      throws InstantiationException, 
             IllegalAccessException, 
             ClassNotFoundException {
    return super.newApplication(
      cl, MockDemoApplication.class.getName(), context);
  }
}
```

我们给出 `MockDemoApplication.class.getName()` 作为类名，这样测试运行器将会加载模拟 application 而不是真实的 application。

## 按应用还是按测试？

此方式与 `setComponent` 有些许不同，因为我们只初始化测试组件一次，而不是每个测试方法执行前都要初始化。确保你在每次测试方法执行前都清除了测试模块的状态，这样每个测试方法都能从零开始执行。

## 源码

我已经在我的两个仓库中使用了此方式：

+ [android-test-demo](https://github.com/chiuki/android-test-demo)：迷你样例演示的此概念。
+ [friendspell](https://github.com/chiuki/friendspell)：一个真实的应用展示了怎样在每个测试之前清除状态。










