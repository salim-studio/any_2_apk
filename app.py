"""any_2_apk: حوّل أي موقع إلى مشروع APK."""
from pathlib import Path
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import io
from generator import build_project_zip, validate_inputs

BASE = Path(__file__).parent
app = Flask(__name__, template_folder=str(BASE / "templates"))
app.secret_key = "any_2_apk-secret"

GENERATED = BASE / "generated"
GENERATED.mkdir(exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        app_name = request.form.get("app_name", "").strip()
        package = request.form.get("package", "").strip()
        url = request.form.get("url", "").strip()
        theme = request.form.get("theme", "#1a73e8").strip()
        icon = request.files.get("icon")
        icon_bytes = icon.read() if icon and icon.filename else None
        if icon_bytes and len(icon_bytes) > 2 * 1024 * 1024:
            flash("حجم الأيقونة يجب أن يكون أقل من 2MB")
            return redirect(url_for("index"))
        errors = validate_inputs(app_name, package, url)
        if errors:
            for e in errors:
                flash(e)
            return redirect(url_for("index"))
        zip_bytes = build_project_zip(app_name, package, url, theme, icon_bytes)
        fname = f"{package}-webview.zip"
        (GENERATED / fname).write_bytes(zip_bytes)
        return render_template("result.html", app_name=app_name, package=package,
                               url=url, fname=fname)
    return render_template("index.html")


@app.route("/download/<fname>")
def download(fname):
    p = GENERATED / fname
    if not p.exists():
        return "الملف غير موجود", 404
    return send_file(p, as_attachment=True)


@app.route("/guide")
def guide():
    return render_template("result.html", app_name="دليل الطرق",
                           package="com.example", url="",
                           fname="", guide_only=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
