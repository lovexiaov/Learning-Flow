# 利用 Espresso 和 Dagger 编写可靠的功能测试

**可靠性**是自动化测试的一个核心要素，这意味着无论执行多少次，无论在什么情况下执行，它的结果应该一致，都通过或都失败。有些测试在某些时候会由于未知原因导致结果失败，这类测试被称为**不可靠的**，这是一个真实存在的问题。有时开发团队会直接放弃一遍又一遍的修复此类不可靠问题，他们会跳过执行该测试。这样，我们就突然失去了保护我们免受必然的回归测试的保护网。单元测试通常会通过模拟所有依赖避免出现此类情况，而功能测试有自己的实现方式。一个经典的例子是在屏幕上加载从网络上获取的数据——在离线状态下，每次执行测试都会失败！那么，我们要如何编写可靠的功能测试而不受网络状况的影响呢？本文我将介绍一种使用 Dagger 创建简洁且健壮的功能测试的方法。

## 什么是 Dagger

[Dagger](http://google.github.io/dagger/) 已经成为众多 Android 开发者军火库中的必备工具，如果你还没听说过它——它是一个快速的[依赖注入](https://en.wikipedia.org/wiki/Dependency_injection)框架，由 [Square](https://squareup.com/) 开发，并针对 Android 做了特别优化。不像其他流行的依赖注入器，Dagger 没有使用反射，而是依靠生成代码提高执行速度。我们将在应用中使用 Dagger 用不种简洁的方法替代依赖，没有破坏代码封装，也不会写多余的只用于测试的代码。还等什么呢！

## 天气应用

我们将会开发一个简单的只有一个界面的天气应用来作为演示。此应用请求用户提供城市名称，然后下载该城市当前天气的信息。如下所示：

![weather.png](/Users/lovexiaov/gitrepo/Learning-Flow/pic/weather.png)

完整的源码托管在 [GitHub](https://github.com/Egorand/android-espresso-dagger-testing) 上。

### OpenWeatherMap API

我们将会使用[OpenWeatherMap API](http://openweathermap.org/api) 来获取天气数据。此 API 是免费的，但是如果你想要在自己机器上下载并编译应用，你需要注册来获取一个 API key。

### 设置 REST API client

下面我们来设置 REST API client 实现获取数据功能。我们将会使用 [Retrofit]() 配合 [RxJava]()完成实现，所以需要将以下依赖加入到 `build.gradle` 中：

```gradle
dependencies {  
    // rest of dependencies

    compile 'com.squareup.retrofit:retrofit:1.9.0'
    compile 'io.reactivex:rxandroid:1.0.1'
}
```  

接下来是一个简单的名为 `WeatherData` 的 POJO，该类将代表我们从服务器上获取的信息。

```java
public class WeatherData {

    public static final String DATE_FORMAT = "EEEE, d MMM";

    private static final int KELVIN_ZERO = 273;

    private static final String FORMAT_TEMPERATURE_CELSIUS = "%d°";
    private static final String FORMAT_HUMIDITY = "%d%%";

    private String name;
    private Weather[] weather;
    private Main main;

    public String getCityName() {
        return name;
    }

    public String getWeatherDate() {
        return new SimpleDateFormat(DATE_FORMAT, Locale.getDefault()).format(new Date());
    }

    public String getWeatherState() {
        return weather().main;
    }

    public String getWeatherDescription() {
        return weather().description;
    }

    public String getTemperatureCelsius() {
        return String.format(FORMAT_TEMPERATURE_CELSIUS, (int) main.temp - KELVIN_ZERO);
    }

    public String getHumidity() {
        return String.format(FORMAT_HUMIDITY, main.humidity);
    }

    private Weather weather() {
        return weather[0];
    }

    private static class Weather {
        private String main;
        private String description;
    }

    private static class Main {
        private float temp;
        private int humidity;
    }
}
```

然后是简单的 Retrofit 接口，该接口包含了我们用来获取数据的 GET 请求的描述：

```java
public interface WeatherApiClient {

    Endpoint ENDPOINT = Endpoints.newFixedEndpoint("http://api.openweathermap.org/data/2.5");

    @GET("/weather") Observable<WeatherData> getWeatherForCity(@Query("q") String cityName);
}
```


以上是针对网络的设置。下面让我们来配置 Dagger 使它能提供一个 `WeatherApiClient` 类的实现供需要的类调用。

### 配置 Dagger

在 `build.gradle` 文件中添加以下几行将 Dagger 配置到你的工程中：

```gradle
final DAGGER_VERSION = '2.0.2'

dependencies {  
    // Retrofit dependencies are here

    compile "com.google.dagger:dagger:${DAGGER_VERSION}"
    apt "com.google.dagger:dagger-compiler:${DAGGER_VERSION}"
    provided 'org.glassfish:javax.annotation:10.0-b28'
}
```

你可能注意到了我们在 `apt` 作用域中引入了 `dagger-compiler`：因为 `dagger-compiler` 是一个注解处理器，我们只希望在编译时期使用它而不想将它打包到 APK 中（就 dex 方法数限制而言 `dagger-compiler` 是十分庞大的）。可以使用 [andrpid-apt](https://bitbucket.org/hvisser/android-apt) 插件来实现此功能。将以下行添加到应用要目录的 `build.gradle` 文件中：

```gradle
buildscript {  
    dependencies {
        // other classpath declarations
        classpath 'com.neenbedankt.gradle.plugins:android-apt:1.8'
    }
}
```

然后在 app 目录下的 `build.gradle` 文件的最上方添加一行：

```gradle
apply plugin: 'com.neenbedankt.android-apt'
```

现在，我们得到了所有需要的依赖。下面我们会创建一个 Dagger 模块，该模块描述了我们提供依赖的逻辑：

```java
@Module
public class AppModule {

    private final Context context;

    public AppModule(Context context) {
        this.context = context.getApplicationContext();
    }

    @Provides @AppScope public Context provideAppContext() {
        return context;
    }

    @Provides public WeatherApiClient provideWeatherApiClient() {
        return new RestAdapter.Builder()
                .setEndpoint(WeatherApiClient.ENDPOINT)
                .setRequestInterceptor(apiKeyRequestInterceptor())
                .setLogLevel(BuildConfig.DEBUG ? RestAdapter.LogLevel.FULL : RestAdapter.LogLevel.NONE)
                .build()
                .create(WeatherApiClient.class);
    }

    private RequestInterceptor apiKeyRequestInterceptor() {
        return new ApiKeyRequestInterceptor(context.getString(R.string.open_weather_api_key));
    }
}
```

如你所见，`provideWeatherApiClient()` 真实的创建了 `WeatherApiClient`的实例，并将其返回：每次我们请求它提供一个 `WeatherApiClient`实例时，这段代码都会被调用。太爽啦！现在我们添加一个 `Component` 接口，该接口描述了 Dagger 创建的我们程序依赖关系图的约定：

```java
@AppScope
@Component(modules = AppModule.class)
public interface AppComponent {

    void inject(MainActivity activity);

    @AppScope Context appContext();

    WeatherApiClient weatherApiClient();
}
```

`AppComponent` 能够提供应用 `Context` 的实例以及 `WeatehrApiClient` 的实例，它还可以向 `MainActivity` 中注入依赖。

最后，我们需要实例化 `AppComponent` 并使它可被其他类使用。我们会将以下代码加入到自定义的 `Application` 类 `WeatherApp` 中：

```java
public class WeatherApp extends Application {

    private AppComponent appComponent;

    @Override
    public void onCreate() {
        super.onCreate();

        appComponent = DaggerAppComponent.builder()
                .appModule(new AppModule(this))
                .build();
    }

    public AppComponent appComponent() {
        return appComponent;
    }
}
```

现在我们可以打开 `MainActivity`看一下我们如何使用 `WeatherApiClient` 获取 天气数据的。

### MainActivity

`MainActivity` 中相关代码（[完整代码](https://github.com/Egorand/android-espresso-dagger-testing/blob/master/app/src/main/java/me/egorand/weather/ui/activities/MainActivity.java)）：

```java
public class MainActivity extends AppCompatActivity implements SearchView.OnQueryTextListener {

    @Inject WeatherApiClient weatherApiClient;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        ((WeatherApp) getApplication()).appComponent().inject(this);
    }

    @Override
    public boolean onQueryTextSubmit(String query) {
        if (!TextUtils.isEmpty(query)) {
            loadWeatherData(query);
        }
        return true;
    }

    private void loadWeatherData(String cityName) {
        subscription = weatherApiClient.getWeatherForCity(cityName)
                .subscribeOn(Schedulers.io())
                .observeOn(AndroidSchedulers.mainThread())
                .subscribe(
                        // handle result
                        }
                );
    }
}
```

请注意看我们如何实例化 `WeatherApiClient` 的：我们没有手动创建，而是使用注解 `@Inject` 标记，并在 `onCreate()` 中做如下操作：

```java
((WeatherApp) getApplication()).appComponent().inject(this);
```
 
 通过访问我们的 `AppComponent` 并将它注入到 `MainActivity` 中， 我们使 Dagger 满足了所有的依赖需求（通过使用 `@Inject` 标记，它出色的完成的任务）。接下来我们就可以使用 `WeatherApiClient` 获取数据了。
 
 尽管此方式乍看起来啰嗦且不简明，它真正强大的地方在于我们不需要硬编码创建依赖。这种优势将在下一步我们需要替代测试代码中的依赖时突显出来。
 
 
### 配置 Espresso 

现在让我们将 Espresso 集成到工程中，并编写测试验证我们能否正常获取数据并展示数据。首先，添加以下依赖到 `build.gradle` 中：

```gradle
final ESPRESSO_VERSION = '2.2.1'  
final ESPRESSO_RUNNER_VERSION = '0.4'

dependencies {  
    // 'compile' dependencies

    androidTestCompile "com.android.support.test:runner:${ESPRESSO_RUNNER_VERSION}"
    androidTestCompile "com.android.support.test:rules:${ESPRESSO_RUNNER_VERSION}"
    androidTestCompile "com.android.support.test.espresso:espresso-core:${ESPRESSO_VERSION}"
    androidTestApt "com.google.dagger:dagger-compiler:${DAGGER_VERSION}"
}
```

这里我们也用到了 `dagger-compiler`，因为我们的测试代码也必须使用注解处理器执行。接下来我们添加一个测试类：

```java
@LargeTest
@RunWith(AndroidJUnit4.class)
public class MainActivityTest {

    private static final String CITY_NAME = "München";

    @Rule public ActivityTestRule<MainActivity> activityTestRule = new ActivityTestRule<>(MainActivity.class);

    @Inject WeatherApiClient weatherApiClient;

    @Before
    public void setUp() {
        weatherApiClient = ((WeatherApp) activityTestRule.getActivity().getApplication()).appComponent()
                .weatherApiClient();
    }

    @Test
    public void correctWeatherDataDisplayed() {
        WeatherData weatherData = weatherApiClient.getWeatherForCity(CITY_NAME).toBlocking().first();

        onView(withId(R.id.action_search)).perform(click());
        onView(withId(android.support.v7.appcompat.R.id.search_src_text)).perform(replaceText(CITY_NAME));
        onView(withId(android.support.v7.appcompat.R.id.search_src_text)).perform(pressKey(KeyEvent.KEYCODE_ENTER));

        onView(withId(R.id.city_name)).check(matches(withText(weatherData.getCityName())));
        onView(withId(R.id.weather_date)).check(matches(withText(weatherData.getWeatherDate())));
        onView(withId(R.id.weather_state)).check(matches(withText(weatherData.getWeatherState())));
        onView(withId(R.id.weather_description)).check(matches(withText(weatherData.getWeatherDescription())));
        onView(withId(R.id.temperature)).check(matches(withText(weatherData.getTemperatureCelsius())));
        onView(withId(R.id.humidity)).check(matches(withText(weatherData.getHumidity())));
    }
}
```
测试用例简洁明了：我们想我为指定城市加载天气数据并验证数据是否正常显示。这在多数情况下应该都是正常的，但想象以下如果在飞行模式下执行呢？很可能会失败！由于我们设计的测试用例时用来验证应用是否能正常显示数据，而不能联网导致的数据缺失不是有效场景，该场景会使我们的测试失败。另外，我们可能会编写另一个测试用例来检查在飞行模式下应用的行为是否正常——如何使这两个测试用例同时执行通过呢？Dagger 可以搞定！让我们利用依赖注入的力量，提供一个可配置我们期望接收数据的 `WeatherApiClient` 的实现。

### MockWeatherApiClient

我们的一个解决方案是一个返回硬编码数据的 `WeatherApiClient`。创建 `TestData` 类，该类中存放了我们期望返回的 JSON 数据。

```java
public final class TestData {

    public static final String MUNICH_WEATHER_DATA_JSON = "\n" +
            "{\n" +
            "    \"coord\": {\n" +
            "        \"lon\": 11.58,\n" +
            "        \"lat\": 48.14\n" +
            "    },\n" +
            "    \"weather\": [{\n" +
            "        \"id\": 741,\n" +
            "        \"main\": \"Fog\",\n" +
            "        \"description\": \"fog\",\n" +
            "        \"icon\": \"50n\"\n" +
            "    }],\n" +
            "    \"base\": \"cmc stations\",\n" +
            "    \"main\": {\n" +
            "        \"temp\": 275.68,\n" +
            "        \"pressure\": 1030,\n" +
            "        \"humidity\": 93,\n" +
            "        \"temp_min\": 274.15,\n" +
            "        \"temp_max\": 277.15\n" +
            "    },\n" +
            "    \"wind\": {\n" +
            "        \"speed\": 1.5,\n" +
            "        \"deg\": 240\n" +
            "    },\n" +
            "    \"clouds\": {\n" +
            "        \"all\": 0\n" +
            "    },\n" +
            "    \"dt\": 1449350400,\n" +
            "    \"sys\": {\n" +
            "        \"type\": 1,\n" +
            "        \"id\": 4887,\n" +
            "        \"message\": 0.0134,\n" +
            "        \"country\": \"DE\",\n" +
            "        \"sunrise\": 1449298092,\n" +
            "        \"sunset\": 1449328836\n" +
            "    },\n" +
            "    \"id\": 6940463,\n" +
            "    \"name\": \"Altstadt\",\n" +
            "    \"cod\": 200\n" +
            "}";

    private TestData() {
        // no instances
    }
}
```

`MockWeatherApiClient` 只需要解析返回的 JSON 数据。我们还可以加入延迟以模仿网络延迟：

```java
public class MockWeatherApiClient implements WeatherApiClient {

    @Override public Observable<WeatherData> getWeatherForCity(String cityName) {
        WeatherData weatherData = new Gson().fromJson(TestData.MUNICH_WEATHER_DATA_JSON, WeatherData.class);
        return Observable.just(weatherData).delay(1, TimeUnit.SECONDS);
    }
}
```

有了可配置的 `WeatherApiClient`，我们不在需要依赖任何的外部状况，我们可以配置它来返回任何我们想要测试的数据。接下来，我们将找出使 `MockWeatherApiClient` 可用的方法。

### 配置 Dagger 测试

我们需要模仿在我们应用代码中的配置步骤，从创建 `TestAppModule` 类开始：

```java
@Module
public class TestAppModule {

    private final Context context;

    public TestAppModule(Context context) {
        this.context = context.getApplicationContext();
    }

    @Provides @AppScope public Context provideAppContext() {
        return context;
    }

    @Provides public WeatherApiClient provideWeatherApiClient() {
        return new MockWeatherApiClient();
    }
}
```

该类与 `AppMoudle` 十分相似，但是我们没有使用 Retrofit 创建真是的 `WeatherApiClient` 的实现，而是简单的实例化了 `MockWeatherApiClient`。接下来添加 `TestAppComponent`：

```java
@AppScope
@Component(modules = TestAppModule.class)
public interface TestAppComponent extends AppComponent {

    void inject(MainActivityTest test);
}
```

`TestAppComponent` 继承了 `AppComonent` 并添加了我们测试类需要的 `inject()` 方法。接下来修改测试类的 `setUp()` 方法：

```java
@Before
public void setUp() {  
    ((TestWeatherApp) activityTestRule.getActivity().getApplication()).appComponent().inject(this);
}
```

最后，我们使用测试替身替换 `WeatherApp`：

```java
public class TestWeatherApp extends WeatherApp {

    private TestAppComponent testAppComponent;

    @Override
    public void onCreate() {
        super.onCreate();

        testAppComponent = DaggerTestAppComponent.builder()
                .testAppModule(new TestAppModule(this))
                .build();
    }

    @Override
    public TestAppComponent appComponent() {
        return testAppComponent;
    }
}
```

注意我们这里返回的是 `TestAppComponent` 而不是 `AppComponent`。 类的接口保持不变，这意味着使用测试替身对应用代码毫无影响。

我们现在配置完了 Dagger，但还遗漏了关键的一点：如何让我们的测试使用 `TestWeatherApp` 而不是 `WeatherApp`？答案是使用自定义测试执行器！

### 实现自定义测试执行器

用来执行 Espresso 测试的 `AndroidJUnitRunner` 有一个便捷的方法 `newApplication()`，我们可以覆写该方法来使用 `TestWeatherApp` 替换 `WeatherApp`：

```java
public class WeatherTestRunner extends AndroidJUnitRunner {

    @Override
    public Application newApplication(ClassLoader cl, String className, Context context) throws InstantiationException,
            IllegalAccessException, ClassNotFoundException {
        String testApplicationClassName = TestWeatherApp.class.getCanonicalName();
        return super.newApplication(cl, testApplicationClassName, context);
    }
}
```

不要忘记在 `build.gradle` 中声明它哟：

```gradle
defaultConfig {  
    // rest of configuration

    testInstrumentationRunner "me.egorand.weather.runner.WeatherTestRunner"
}
```

这样就可以了！我们可以使用以下命令执行测试：

```shell
./gradlew connectedAndroidTest
```

至此，我们已经完成不受网络影响执行功能测试的配置，并保证了测试结果正常执行。请到 [GitHub](https://github.com/Egorand/android-espresso-dagger-testing)` 上查看本文用到的完整源码。

## 结论

正如我在[使用 Espresso 测试一个有序列表（中译版）](http://www.jianshu.com/p/9c61db4be5c5)中所说，有一套验收测试是一种 catch regressions 的很好方式，并且保证了绝大多数的 bug 会被开发团队发现，而不是终端用户。那么保证你测试的可靠性就变得十分重要：不可靠的测试只会浪费团队的时间去一遍一遍的修复它们，直到所有人都决定不去执行这些测试。

通过使用 Dagger 我们可以使代码与依赖注入逻辑解耦，这将允许我们使用测试替身并且控制待测应用的某些方面。本文描述了使用此技术允许在离线模式下执行网络相关的测试，并保证它们正常执行。值得一提的是，此方法不适用于端对端的测试，因为我们没有像用户一样在真实环境中测试应用。然而，这仍然是一个非常有效的执行功能测试的方法，也使你能很灵活的测试应用各方面逻辑。

你有在自己的 Espresso 中使用 Dagger 吗？希望能与你交流。如果你有任何反馈或发现文中错误，欢迎留言或直接与我联系，祝好！




















