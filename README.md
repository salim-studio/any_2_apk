# any_2_apk 📱

حوّل أي موقع ويب إلى مشروع أندرويد (WebView) جاهز للبناء إلى APK.

## التشغيل

```
pip install -r requirements.txt
python app.py
```

ثم افتح: http://localhost:5000

## الاستخدام
1. أدخل اسم التطبيق + اسم الحزمة (مثال: com.example.myapp) + رابط الموقع
2. حمّل ملف ZIP الناتج
3. ارفعه إلى GitHub → تبويب Actions → حمّل `app-debug.apk`
   أو افتحه في Android Studio → Run

## تنبيه صادق
لا يوجد تحويل مباشر من exe إلى APK. الطريقة الصحيحة: تغليف نسخة الويب (هذا التطبيق) أو إعادة البناء بـ Flutter/Kotlin.
