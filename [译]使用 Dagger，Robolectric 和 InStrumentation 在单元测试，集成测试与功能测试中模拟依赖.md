# 使用 Dagger，Robolectric 和 InStrumentation 在单元测试，集成测试与功能测试中模拟依赖

> 原文：[How to mock dependencies in Unit, Integration and Functional tests; Dagger, Robolectric and Instrumentation](http://artemzin.com/blog/how-to-mock-dependencies-in-unit-integration-and-functional-tests-dagger-robolectric-instrumentation/#)
> 
> 作者：[Artem Zinnatullin](http://artemzin.com/blog/author/artem/)
> 
> 译者：[lovexiaov](http://www.jianshu.com/users/7378dce2d52c/latest_articles)

亲爱的读者，你好。

最初，这只是一个对 Reddit 上 [Robolectric and Dagger 2](https://www.reddit.com/r/androiddev/comments/3y024f/robolectric_and_dagger_2/) 的评论。但是由于内容很多所以我决定将它总结为一篇博客，祝您阅读愉快。

---

## 依赖注入（DI）框架 & 单元测试

单元测试中，我们经常隔离测试一个类或方法。如果被测试的是有行为的类，如`RestApi`，`DataManager`等，你需要模拟它的依赖；如果被依赖的是“值类”，如`User`，`Message`等，你可以直接使用它们（也可以模拟它们）。

这意味着通常我们并不需要在单元测试中使用 DI 框架，因为单元测试目标只是一个类或一个方法，而不是几个类。目标类应该通过以下方式获取依赖：

+ 通过构造方法（推荐方式）
+ 通过方法或字段

99% 的单元测试都不需要 DI 框架，通常只有像`Activity`，`Fragment`，`View`或`Service`这样在创建以后需要一系列依赖的类需要与 DI 框架交互。然而，我提倡使用 MVP 等模式将逻辑从 Android 框架类中移出，并且使用功能（UI）测试而不是单元测试来覆盖它们。

## DI 框架 & 集成测试

一般而言，你也不必在集成测试中使用 DI 框架。因为集成测试只是简单的将几个类关联起来测试它们的继承。如果你的代码是依赖注入友好的（DI-friendly），你可以不使用 DI 框架将需要的依赖传入。

> 如果你确实需要通过 DI 框架提供模拟依赖，并且你使用了 Robolectric，请继续往下看。

## DI 框架 & 功能（UI）测试

此类测试确实需要使用 DI 框架模拟依赖。因为一般来说，功能测试针对的是真个应用，而不是几个类。

如果你需要在`instrumentation`测试（Espresso，Robotium，或单纯的 instrumentation 测试等）使用 DI 框架，请继续往下看。

## 如何使用 Dagger 2 和 Robolectric 在测试中模拟并注入依赖？
(通常适用于集成测试)

> **主要思路**：对于 Roboletric 测试，可以自定义一个`Application`类，在其中模拟依赖。

你可以在 application 类中定义一个返回`DaggerAppComponent`的内部类` Builder`类对象，然后在集成测试时使用使用适当的子类覆盖该 application 类！

**application 类**

```java
  public class MyApp extends Application {

  @NonNull // Initialized in onCreate.
  AppCompontent appComponent;

  @Override
  public void onCreate() {
    appComponent = prepareAppComponent().build();
  }

  // Here is the trick, we allow extend application class and modify AppComponent.
  @NonNull
  protected DaggerAppComponent.Builder prepareAppComponent() {
    return new DaggerAppComponent.Builder();
  }
}
```

**用于集成测试的 application 类**

```java
public class MyIntegrationTestApp extends MyApp {

  @Override
  @NonNull
  protected DaggerAppComponent.Builder prepareAppComponent() {
    return super.prepareAppComponent()
      .someModule(new SomeModule() {
        @Override
        public SomeDependency provideSomeDependency(@NonNull SomeArgs someArgs) {
          return mock(SomeDependency.class); // You can provide any kind of mock you need.
        }
      })
  }
}
```
然后通过自定义`RobolectricGradleTestRunner`类使用该类。

**自定义带有定制化 application 类的 Robolectric 测试执行器**

```java
public class IntegrationRobolectricTestRunner extends RobolectricGradleTestRunner {

    // This value should be changed as soon as Robolectric will support newer api.
    private static final int SDK_EMULATE_LEVEL = 21;

    public IntegrationRobolectricTestRunner(@NonNull Class<?> clazz) throws Exception {
        super(clazz);
    }

    @Override
    public Config getConfig(@NonNull Method method) {
        final Config defaultConfig = super.getConfig(method);
        return new Config.Implementation(
                new int[]{SDK_EMULATE_LEVEL},
                defaultConfig.manifest(),
                defaultConfig.qualifiers(),
                defaultConfig.packageName(),
                defaultConfig.resourceDir(),
                defaultConfig.assetDir(),
                defaultConfig.shadows(),
                MyIntegrationTestApp.class, // Here is the trick, we change application class to one with mocks.
                defaultConfig.libraries(),
                defaultConfig.constants() == Void.class ? BuildConfig.class : defaultConfig.constants()
        );
    }
}
```

## 如何在 Instrumentation 测试中使用 Dagger 2 模拟并注入依赖？

Google 的那帮兄弟建议使用 [flavors](http://android-developers.blogspot.ru/2015/12/leveraging-product-flavors-in-android.html)，但我并不推荐使用它。因为 flavors 越多，构建应用化肥的时间越长，你也会越不喜欢 Gradle 以及整个构建过程。如果可以避免，尽量不要使用 flavors。

> **主要思路**：与 Roboletric 测试相似——通过修改`Application`类来实现，不过这次是针对 Instrumentation 测试。

为了实现此方法，你需要自定义 Instrumentation 测试执行器，并将它们添加到` build.gradle`中。

```java
public class CustomInstrumentationTestRunner extends AndroidJUnitRunner {

  @Override
  @NonNull
  public Application newApplication(@NonNull ClassLoader cl, 
                                    @NonNull String className, 
                                    @NonNull Context context)
                                    throws InstantiationException, 
                                    IllegalAccessException, 
                                    ClassNotFoundException {
    return Instrumentation.newApplication(CustomApp.class, context);
  }
}
```
将该类添加到`build.gradle`中：

```gradle
android {  
  defaultConfig {
    testInstrumentationRunner 'a.b.c.CustomInstrumentationTestRunner'
  }
}
```
**代码示例**：我已经将内容更新到[ #qualitymatters app](https://github.com/artem-zinnatullin/qualitymatters)中，并做了分析，展示了在单元测试，集成测试和功能测试中模拟依赖的方式。 因为我们在测试真正应用时需要分析，但在实验中却不想分析！也许你已经注意到了，我们没有添加 flavors。

你可以看一下[提交请求详情](https://github.com/artem-zinnatullin/qualitymatters/pull/74)。
