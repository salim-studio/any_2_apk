"""any_2_apk: مولد مشروع أندرويد WebView جاهز للبناء إلى APK."""
import io
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse

PACKAGE_RE = re.compile(r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$')


def validate_inputs(app_name: str, package: str, url: str) -> list[str]:
    errors = []
    if not app_name or len(app_name.strip()) < 2:
        errors.append("اسم التطبيق قصير جداً.")
    if not PACKAGE_RE.match(package.strip()):
        errors.append("اسم الحزمة غير صالح. مثال صحيح: com.example.myapp")
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        errors.append("الرابط غير صالح. يجب أن يبدأ بـ https://")
    return errors


def java_path(package: str) -> str:
    return "app/src/main/java/" + package.replace(".", "/") + "/MainActivity.kt"


MANIFEST_TMPL = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <application
        android:label="{app_name}"
        android:icon="@mipmap/ic_launcher"
        android:theme="@style/Theme.WebToApk"
        android:usesCleartextTraffic="{cleartext}">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

MAIN_ACTIVITY_TMPL = """package {package}

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout

class MainActivity : AppCompatActivity() {{
    private lateinit var webView: WebView
    private lateinit var swipe: SwipeRefreshLayout
    private val startUrl = "{url}"

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        webView = findViewById(R.id.webview)
        swipe = findViewById(R.id.swipe)
        val s: WebSettings = webView.settings
        s.javaScriptEnabled = true
        s.domStorageEnabled = true
        s.mediaPlaybackRequiresUserGesture = false
        s.loadWithOverviewMode = true
        s.useWideViewPort = true
        webView.webViewClient = object : WebViewClient() {{
            override fun shouldOverrideUrlLoading(view: WebView, req: WebResourceRequest): Boolean {{
                return false  // ابق داخل التطبيق
            }}
        }}
        webView.webChromeClient = WebChromeClient()
        swipe.setOnRefreshListener {{ webView.reload() }}
        webView.loadUrl(startUrl)
    }}

    override fun onBackPressed() {{
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack()
        else super.onBackPressed()
    }}
}}
"""

LAYOUT = """<?xml version="1.0" encoding="utf-8"?>
<androidx.swiperefreshlayout.widget.SwipeRefreshLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/swipe"
    android:layout_width="match_parent"
    android:layout_height="match_parent">
    <WebView
        android:id="@+id/webview"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />
</androidx.swiperefreshlayout.widget.SwipeRefreshLayout>
"""

BUILD_GRADLE_APP = """plugins {{ id 'com.android.application'; id 'org.jetbrains.kotlin.android' }}
android {{
    namespace '{package}'
    compileSdk 34
    defaultConfig {{
        applicationId '{package}'
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }}
    buildTypes {{
        release {{ minifyEnabled false }}
    }}
}}
dependencies {{
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:1.11.0'
    implementation 'androidx.swiperefreshlayout:swiperefreshlayout:1.1.0'
}}
"""

GITHUB_WORKFLOW = """name: Build APK
on: [push, workflow_dispatch]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: {{ distribution: temurin, java-version: 17 }}
      - uses: gradle/actions/setup-gradle@v3
      - run: chmod +x gradlew
      - run: ./gradlew assembleDebug
      - uses: actions/upload-artifact@v4
        with: {{ name: app-debug, path: app/build/outputs/apk/debug/app-debug.apk }}
"""


def build_project_zip(app_name: str, package: str, url: str,
                      theme_color: str = "#1a73e8",
                      icon_bytes: bytes | None = None) -> bytes:
    """يرجع ملف ZIP لمشروع أندرويد كامل."""
    package = package.strip()
    url = url.strip()
    app_name = app_name.strip()
    allow_http = urlparse(url).scheme == "http"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("settings.gradle", "pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }\ndependencyResolutionManagement { repositories { google(); mavenCentral() } }\nrootProject.name = \"" + app_name + "\"\ninclude ':app'\n")
        z.writestr("app/build.gradle", BUILD_GRADLE_APP.format(package=package))
        z.writestr("app/src/main/AndroidManifest.xml", MANIFEST_TMPL.format(app_name=app_name, cleartext=str(allow_http).lower()))
        z.writestr(java_path(package), MAIN_ACTIVITY_TMPL.format(package=package, url=url))
        z.writestr("app/src/main/res/layout/activity_main.xml", LAYOUT)
        z.writestr("app/src/main/res/values/strings.xml", f'<resources><string name="app_name">{app_name}</string></resources>')
        z.writestr("app/src/main/res/values/themes.xml", f'<resources><style name="Theme.WebToApk" parent="Theme.Material3.DayNight.NoActionBar"><item name="colorPrimary">{theme_color}</item></style></resources>')
        z.writestr(".github/workflows/build-apk.yml", GITHUB_WORKFLOW)
        z.writestr("README_BUILD_AR.md", (
            f"# {app_name}\n\nمشروع WebView لـ {url}\n\n"
            "## بناء APK محلياً\n1. افتح المجلد في Android Studio\n2. Run > Run app (يولد APK)\n3. أو: `./gradlew assembleDebug` → تجد الملف في `app/build/outputs/apk/debug/app-debug.apk`\n\n"
            "## بناء سحابي مجاني (بدون تثبيت)\n1. ارفع هذا المشروع إلى GitHub\n2. تبويب Actions → ستحصل على ملف `app-debug.apk` جاهز للتحميل\n\n"
            "## ملاحظة مهمة\nلا يمكن تحويل ملفات exe أو برامج سطح المكتب إلى APK تلقائياً. "
            "الطريقة الصحيحة هي تغليف نسخة الويب بـ WebView (هذا المشروع) أو إعادة بناء التطبيق بـ Flutter/Kotlin.\n"
        ))
        if icon_bytes:
            # نضع الأيقونة الخام + تعليمات؛ التحجيم الكامل يتم في Android Studio عبر Image Asset
            z.writestr("icon-original.png", icon_bytes)
    buf.seek(0)
    return buf.getvalue()
