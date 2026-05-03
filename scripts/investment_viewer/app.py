from flask import Flask, render_template, abort, jsonify
import os, re, subprocess
from datetime import datetime

app = Flask(__name__)
BASE = os.path.expanduser("~/Desktop/claude")
SEND_TO = "li.lance320@gmail.com"


def current_date():
    return datetime.today().strftime("%Y-%m-%d")


def scan_weeks():
    out = []
    if not os.path.isdir(BASE):
        return out
    for name in sorted(os.listdir(BASE), reverse=True):
        path = os.path.join(BASE, name)
        if not os.path.isdir(path):
            continue
        try:
            datetime.strptime(name, "%Y-%m-%d")
        except ValueError:
            continue
        out.append({
            "week": name,
            "has_report": os.path.exists(os.path.join(path, "report.html")),
        })
    return out


def parse_html(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    styles = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", raw, re.DOTALL | re.IGNORECASE))
    m = re.search(r"<body[^>]*>(.*?)</body>", raw, re.DOTALL | re.IGNORECASE)
    body = m.group(1) if m else raw
    return styles, body


@app.route("/")
def index():
    today = current_date()
    today_folder = os.path.join(BASE, today)
    this_week = {
        "week": today,
        "has_report": os.path.exists(os.path.join(today_folder, "report.html")),
        "folder_exists": os.path.isdir(today_folder),
    }
    return render_template("index.html", weeks=scan_weeks(), this_week=this_week)


@app.route("/report/<week>")
def report(week):
    try:
        datetime.strptime(week, "%Y-%m-%d")
    except ValueError:
        abort(400)
    path = os.path.join(BASE, week, "report.html")
    if not os.path.exists(path):
        abort(404)
    styles, body = parse_html(path)
    return render_template(
        "viewer.html",
        styles=styles,
        body=body,
        week=week,
        send_to=SEND_TO,
        weeks=scan_weeks(),
    )


@app.route("/generate")
def generate():
    today = current_date()
    today_folder = os.path.join(BASE, today)

    # Create date folder only (no subfolders)
    os.makedirs(today_folder, exist_ok=True)

    already_has_report = os.path.exists(os.path.join(today_folder, "report.html"))

    # Open Terminal and run claude
    script = f'''tell application "Terminal"
    activate
    do script "cd ~/Desktop/claude/{today} && claude \\"做分析\\""
end tell'''
    try:
        subprocess.Popen(["osascript", "-e", script])
        status = "launched"
    except Exception as e:
        status = f"error: {e}"

    return jsonify({
        "week": today,
        "folder": today_folder,
        "already_has_report": already_has_report,
        "status": status,
    })


@app.route("/status/<week>")
def status(week):
    try:
        datetime.strptime(week, "%Y-%m-%d")
    except ValueError:
        abort(400)
    folder = os.path.join(BASE, week)
    return jsonify({
        "week": week,
        "has_report": os.path.exists(os.path.join(folder, "report.html")),
        "folder_exists": os.path.isdir(folder),
    })


if __name__ == "__main__":
    print("投资报告查看器启动中 → http://localhost:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)
