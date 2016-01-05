> 原文：[Testing a sorted list with Espresso](http://blog.egorand.me/testing-a-sorted-list-with-espresso/)
> 作者：[Egor Andreevici](https://twitter.com/EgorAnd)
> 译者：[lovexiaov](http://www.jianshu.com/users/7378dce2d52c/latest_articles)

Espresso 是一个十分强大的工具，可以用它为 Android 编写验收测试。所谓[验收测试](https://en.wikipedia.org/wiki/Acceptance_testing#Acceptance_testing_in_extreme_programming)是指正确实现了所有特性（或某些方面的特性）。自动化验收测试的优势在于简单的捕捉回归，这在积极开发阶段和 bug 修复阶段很常见。在你写完自动化测试之后，查看新的修改是否引入了问题将变得简单。太棒啦！

本文将向你展示如何在你的 Android 工程中设置 Espresso，并会写一个简单的验收测试来检验一组英超联赛团队是否按字母顺序排序。给自己冲杯咖啡（译者注：Espresso 是一种咖啡）并系好你的安全带哟！

## Espresso 设置

如果你使用 Android Studio 和 Gradle，那么配置 Espresso 对你来说将非常简单。你只需要打开 `app` 模块下的 `build.gradle` 文件，并添加以下依赖：

```gradle
def APPCOMPAT_VERSION = "23.1.1"  
def ESPRESSO_RUNNER_VERSION = "0.4.1"

dependencies {  
    // dependencies with "compile" scope go here

    androidTestCompile "com.android.support:support-annotations:${APPCOMPAT_VERSION}"
    androidTestCompile 'com.android.support.test.espresso:espresso-core:2.2.1'
    androidTestCompile "com.android.support.test:runner:${ESPRESSO_RUNNER_VERSION}"
    androidTestCompile "com.android.support.test:rules:${ESPRESSO_RUNNER_VERSION}"
}
```
顺便说一下，此工程的完整代码可托管在[GitHub](https://github.com/Egorand/android-espresso-sorted-list)上，你可以免费获取。

使用 Gradle 同步你的工程，在 Gradle 构建时你可以抿一口咖啡。完成配置还有最后一步，在 `build.gradle` 文件的 `defaultConfig` 语句块中添加如下一行：

```gradle
defaultConfig {  
    // default setup here

    testInstrumentationRunner "android.support.test.runner.AndroidJUnitRunner"
}
```

这样我们就完成了所有配置，让我们开始使用 Espresso 编写验收测试吧。

## 编写验收测试

想必你应该注意到了 `androidTest` 文件夹在 `src` 目录下：Espresso 测试通常就写在这里。创建一个名为 `TeamsActivityTest` 的类，然后添加一对注解如下所示：

```java
@RunWitch(AndroidJunit4.class)
@LargeTest
public class TeamsActivityTest {
}
```
我们在代码中声明了将会使用 JUnit 4 来编写测试。[@LargeTest](http://developer.android.com/reference/android/test/suitebuilder/annotation/LargeTest.html)注解向测试执行器指示了该类包含什么类型的测试，它经常在 Espresso 测试中出现。下面我们将会在测试类中添加以下字段：

```java
@Rule public ActivityTestRule<TeamsActivity> activityTestRule = new ActivityTestRule<>(TeamsActivity.class);
```

在 JUnit 4 引入之前 Android 测试类通常继承自 [ActivityInstrumentationTestCase2]()。使用 JUnit 4 并在测试类中添加被 `@Rule` 注解的 [ActivityTestRule]()类型的字段就足以描述待测 `Activity` 如何被启动了。查看 `ActivityTestRule` 的几个构造方法找到合适测试启动的那个。

让我们继续在我们的测试类中实现测试用例：

```java
@Test 
public void teamsListIsSortedAlphabetically() {  
    onView(withId(android.R.id.list)).check(matches(isSortedAlphabetically()));
}
```

`onView()`，`withId()` 和 `matches()` 都是框架中的静态方法，所以我建议使用静态导入来时测试定义看起来简洁明了。在 GitHub 中的 [示例代码](https://github.com/Egorand/android-espresso-sorted-list/blob/master/app/src/androidTest/java/me/egorand/teams/TeamsActivityTest.java)中查看中学的导入。

`isSortedAlphabetically()` 是一个自定义的 [Hamcrest 匹配器](http://hamcrest.org/JavaHamcrest/javadoc/1.3/org/hamcrest/Matcher.html)，描述了我们想检查我们的 `View`，换句话说，检查 `android.R.id.list` 中的内容是否按字母顺序排序。下面是匹配器的定义：

```java
private static Matcher<View> isSortedAlphabetically() {  
    return new TypeSafeMatcher<View>() {

        private final List<String> teamNames = new ArrayList<>();

        @Override
        protected boolean matchesSafely(View item) {
            RecyclerView recyclerView = (RecyclerView) item;
            TeamsAdapter teamsAdapter = (TeamsAdapter) recyclerView.getAdapter();
            teamNames.clear();
            teamNames.addAll(extractTeamNames(teamsAdapter.getTeams()));
            return Ordering.natural().isOrdered(teamNames);
        }

        private List<String> extractTeamNames(List<Team> teams) {
            List<String> teamNames = new ArrayList<>();
            for (Team team : teams) {
                teamNames.add(team.name);
            }
            return teamNames;
        }

        @Override
        public void describeTo(Description description) {
            description.appendText("has items sorted alphabetically: " + teamNames);
        }
    };
}
```

由于我们知道使用的是 `RecyclerView`，所以我们可以安全的转换 `matchesSafely()` 的参数，并取出 `TeamsAdapter` 以得到其中的数据。我们使用 `extractNames()` 方法从列表中取出 `Team` 对象的名称，然后使用 Guava 的 [Ordering](http://docs.guava-libraries.googlecode.com/git/javadoc/com/google/common/collect/Ordering.html) 类检查列表是否正确的排序。编写 Hamcrest 匹配器时，不要忽视 `describeTo()` 方法，它在测试失败时非常有用。在我们的 `describeTo()` 中，我们简短的描述了匹配器做了什么并会打印我们保存的数据：现在，当测试失败时，我们将会明确知道数据集合是什么样的并得出测试失败的原因。

现在，你可能会有疑问：`Team` 和 `TeamAdapter`（或我们还没有集成的 `RecyclerView`）来自哪里呢？编写测试，甚至不编译是非常好的[测试驱动开发（TDD）](https://en.wikipedia.org/wiki/Test-driven_development)方式。该方式引入了“红-绿-重构”循环：编写测试，使它们编译通过，重构以提出重复代码。我们现在在“红”阶段，接下来让我们编写一些代码进入“绿”阶段。

首先，通过在 `app/build.gradle` 中添加以下依赖集成 `RecyclerView`：

```gradle
dependencies {  
    // other "compile" dependencies go here
    compile "com.android.support:recyclerview-v7:${APPCOMPAT_VERSION}"

    // "androidTest" dependencies are here
}
``` 
如果在你的工程中已经有了一个 `MainActivity`,请将它重命名为 `TeamsActivity`，或者直接创建。`TeamsActivity` 将使用这个[布局](https://github.com/Egorand/android-espresso-sorted-list/blob/master/app/src/main/res/layout/activity_main.xml)。`Team` 是我们的实体类（POJO），代码如下所示：

```java
public class Team {

    public final String name;
    public final @DrawableRes int logoRes;

    public Team(@NonNull String name, @DrawableRes int logoRes) {
        this.name = name;
        this.logoRes = logoRes;
    }

    public static final Comparator<Team> BY_NAME_ALPHABETICAL = new Comparator<Team>() {
        @Override public int compare(Team lhs, Team rhs) {
            return lhs.name.compareTo(rhs.name);
        }
    };
}
```

请注意 `BY_NAME_ALPHABETICAL` 比较器——我们将使用它来按需排序 `Team` 对象。

下面是 `TeamAdapter` 类，简洁易懂：

```java
public class TeamsAdapter extends RecyclerView.Adapter<TeamsAdapter.ViewHolder> {

    private final LayoutInflater layoutInflater;

    private final List<Team> teams;

    public TeamsAdapter(LayoutInflater layoutInflater) {
        this.layoutInflater = layoutInflater;
        this.teams = new ArrayList<>();
    }

    @Override
    public ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        return new ViewHolder(layoutInflater.inflate(R.layout.row_team, parent, false));
    }

    @Override
    public void onBindViewHolder(ViewHolder holder, int position) {
        Team team = teams.get(position);
        holder.teamLogo.setImageResource(team.logoRes);
        holder.teamName.setText(team.name);
    }

    @Override public int getItemCount() {
        return teams.size();
    }

    public void setTeams(List<Team> teams) {
        this.teams.clear();
        this.teams.addAll(teams);
        notifyItemRangeInserted(0, teams.size());
    }

    public List<Team> getTeams() {
        return Collections.unmodifiableList(teams);
    }

    static class ViewHolder extends RecyclerView.ViewHolder {

        ImageView teamLogo;
        TextView teamName;

        public ViewHolder(View itemView) {
            super(itemView);
            teamLogo = (ImageView) itemView.findViewById(R.id.team_logo);
            teamName = (TextView) itemView.findViewById(R.id.team_name);
        }
    }
}
```

`row_team` 的布局在[这里](https://github.com/Egorand/android-espresso-sorted-list/blob/master/app/src/main/res/layout/row_team.xml)。现在，让我们添加代码来为 `TeamActivity` 创建 `Team` 对象并初始化 `TeamAdapter`：

```java
@Override
protected void onCreate(Bundle savedInstanceState) {  
    super.onCreate(savedInstanceState);
    setContentView(R.layout.activity_main);

    RecyclerView teamsRecyclerView = (RecyclerView) findViewById(android.R.id.list);
    teamsRecyclerView.setLayoutManager(new LinearLayoutManager(this));

    TeamsAdapter teamsAdapter = new TeamsAdapter(LayoutInflater.from(this));
    teamsAdapter.setTeams(createTeams());
    teamsRecyclerView.setAdapter(teamsAdapter);
}

private List<Team> createTeams() {  
    List<Team> teams = new ArrayList<>();
    String[] teamNames = getResources().getStringArray(R.array.team_names);
    TypedArray teamLogos = getResources().obtainTypedArray(R.array.team_logos);
    for (int i = 0; i < teamNames.length; i++) {
        Team team = new Team(teamNames[i], teamLogos.getResourceId(i, -1));
        teams.add(team);
    }
    teamLogos.recycle();
    Collections.sort(teams, Team.BY_NAME_ALPHABETICAL);
    return teams;
}
```

我们在把列表传入适配器之前使用 `Team.BY_NAME_ALPHABETICAL` 适当的进行排序。

请通过 [GitHub](https://github.com/Egorand/android-espresso-sorted-list)上的示例将代码补全。

代码编写完了！现在你可以通过右击 `TeamsActivityTest` 类选择“Run”命令来执行测试，也可以在命令行中执行如下命令：

```shell
./gradlew connectedAndroidTest
```

测试会执行通过，就算测试失败，通常我们也会得到 Espresso 非常有用的输出信息来帮助我们调试问题。

现在，我们使用 Espresso 编写了回归测试，该测试会自动检查我们已经实现的功能是否正常。如上文所说，[GitHub](https://github.com/Egorand/android-espresso-sorted-list)上有完整的示例代码。

你有使用 Espresso 编写测试验证你的功能吗？希望能与你交流。如果你有任何反馈或发现文中错误，欢迎留言或直接与我联系，干杯！
