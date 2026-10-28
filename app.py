
import os
import sqlite3
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash
)

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "development-key-change-later"
)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "monitor.db"
)


def get_db():
    db = sqlite3.connect(DATABASE, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS websites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'UNKNOWN',
                response_time REAL,
                status_code INTEGER,
                last_checked TEXT
            )
        """)

        # Upgrade the database created in earlier steps.
        columns = {
            row["name"]
            for row in db.execute(
                "PRAGMA table_info(websites)"
            ).fetchall()
        }

        migrations = {
            "status": "TEXT NOT NULL DEFAULT 'UNKNOWN'",
            "response_time": "REAL",
            "status_code": "INTEGER",
            "last_checked": "TEXT"
        }

        for column, definition in migrations.items():
            if column not in columns:
                db.execute(
                    f"ALTER TABLE websites ADD COLUMN "
                    f"{column} {definition}"
                )

        db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                response_time REAL,
                status_code INTEGER,
                checked_at TEXT NOT NULL
            )
        """)


def perform_check(site):
    start = time.perf_counter()
    status = "DOWN"
    status_code = None

    try:
        response = requests.get(
            site["url"],
            timeout=5,
            allow_redirects=True,
            headers={"User-Agent": "WebsiteUptimeMonitor/1.0"}
        )
        status_code = response.status_code
        status = "UP" if 200 <= status_code < 400 else "DOWN"
    except requests.RequestException:
        pass

    response_time = round(
        (time.perf_counter() - start) * 1000, 2
    )
    checked_at = datetime.now(timezone.utc).isoformat()

    with get_db() as db:
        db.execute("""
            UPDATE websites
            SET status = ?, response_time = ?,
                status_code = ?, last_checked = ?
            WHERE id = ?
        """, (
            status, response_time, status_code,
            checked_at, site["id"]
        ))

        db.execute("""
            INSERT INTO history
            (website_id, name, url, status, response_time,
             status_code, checked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            site["id"], site["name"], site["url"],
            status, response_time, status_code, checked_at
        ))


def refresh_all():
    with get_db() as db:
        sites = db.execute(
            "SELECT * FROM websites ORDER BY id DESC"
        ).fetchall()

    for site in sites:
        perform_check(site)


@app.route("/")
def home():
    with get_db() as db:
        sites = db.execute(
            "SELECT * FROM websites ORDER BY id DESC"
        ).fetchall()

    total = len(sites)
    up_count = sum(site["status"] == "UP" for site in sites)
    down_count = sum(site["status"] == "DOWN" for site in sites)

    return render_template(
        "index.html",
        websites=sites,
        total=total,
        up_count=up_count,
        down_count=down_count
    )


@app.route("/add", methods=["GET", "POST"])
def add_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()
        parsed = urlparse(url)

        if (
            not name
            or parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            flash("Enter a valid website name and HTTP/HTTPS URL.")
            return redirect(url_for("add_page"))

        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO websites (name, url) VALUES (?, ?)",
                    (name, url)
                )

            flash("Website added successfully!")
        except sqlite3.IntegrityError:
            flash("This website URL already exists.")

        return redirect(url_for("websites_page"))

    return render_template("add.html")


@app.route("/websites")
def websites_page():
    with get_db() as db:
        sites = db.execute(
            "SELECT * FROM websites ORDER BY id DESC"
        ).fetchall()

    return render_template("websites.html", websites=sites)


@app.route("/check", methods=["GET", "POST"])
def check_all():
    refresh_all()
    flash("Website checks completed.")
    return redirect(url_for("websites_page"))


@app.route("/check/<int:website_id>", methods=["POST"])
def check_one(website_id):
    with get_db() as db:
        site = db.execute(
            "SELECT * FROM websites WHERE id = ?",
            (website_id,)
        ).fetchone()

    if site:
        perform_check(site)
        flash("Website check completed.")
    else:
        flash("Website not found.")

    return redirect(url_for("websites_page"))


@app.route("/delete/<int:website_id>", methods=["POST"])
def delete_website(website_id):
    with get_db() as db:
        db.execute(
            "DELETE FROM websites WHERE id = ?",
            (website_id,)
        )

    flash("Website removed.")
    return redirect(url_for("websites_page"))


@app.route("/history")
def history_page():
    with get_db() as db:
        records = db.execute("""
            SELECT * FROM history
            ORDER BY id DESC LIMIT 100
        """).fetchall()

    return render_template("history.html", history=records)


@app.route("/health")
def health():
    return {"status": "ok"}, 200


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
