import os
import uuid
import sqlite3
from datetime import datetime
from flask import (
    Flask, request, jsonify, send_from_directory,
    render_template, session, abort
)
from werkzeug.utils import secure_filename
from functools import wraps

# ─────────────────────────────────────────
#  CONFIG  – only change these two
# ─────────────────────────────────────────
ADMIN_PASSWORD = "admin@123"        # ← your admin password
SECRET_KEY     = "docvault-secret"  # ← any random string
MAX_FILE_MB    = 50
# ─────────────────────────────────────────

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH       = os.path.join(BASE_DIR, "docvault.db")

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_MB * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ── Database setup ────────────────────────
def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = get_db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            original_name TEXT    NOT NULL,
            stored_name   TEXT    NOT NULL UNIQUE,
            size_bytes    INTEGER NOT NULL DEFAULT 0,
            mime_type     TEXT    DEFAULT '',
            uploaded_at   TEXT    NOT NULL
        )
    """)
    con.commit()
    con.close()


# ── Helpers ───────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ── Routes ────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", max_mb=MAX_FILE_MB)


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if data.get("password") == ADMIN_PASSWORD:
        session["is_admin"] = True
        return jsonify({"ok": True})
    return jsonify({"error": "Wrong password"}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/session")
def check_session():
    return jsonify({"is_admin": bool(session.get("is_admin"))})


@app.route("/api/documents")
def list_documents():
    con = get_db()
    rows = con.execute(
        "SELECT id, original_name, size_bytes, mime_type, uploaded_at "
        "FROM documents ORDER BY uploaded_at DESC"
    ).fetchall()
    con.close()
    result = []
    for row in rows:
        result.append({
            "id":            row["id"],
            "original_name": row["original_name"],
            "size_human":    human_size(row["size_bytes"]),
            "mime_type":     row["mime_type"],
            "uploaded_at":   row["uploaded_at"][:10],   # YYYY-MM-DD
        })
    return jsonify(result)


@app.route("/api/upload", methods=["POST"])
@admin_required
def upload():
    if "files" not in request.files:
        return jsonify({"error": "No files received"}), 400

    files = request.files.getlist("files")
    saved = []

    for f in files:
        if not f.filename:
            continue
        original = secure_filename(f.filename)
        if not original:
            continue

        ext    = os.path.splitext(original)[1].lower()
        stored = uuid.uuid4().hex + ext
        dest   = os.path.join(UPLOAD_FOLDER, stored)

        f.save(dest)
        size = os.path.getsize(dest)

        con = get_db()
        cur = con.execute(
            "INSERT INTO documents (original_name, stored_name, size_bytes, mime_type, uploaded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (original, stored, size,
             f.mimetype or "application/octet-stream",
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        con.commit()
        doc_id = cur.lastrowid
        con.close()

        saved.append({"id": doc_id, "name": original})

    return jsonify({"uploaded": saved})


@app.route("/api/download/<int:doc_id>")
def download(doc_id):
    con = get_db()
    row = con.execute(
        "SELECT original_name, stored_name FROM documents WHERE id = ?",
        (doc_id,)
    ).fetchone()
    con.close()

    if not row:
        abort(404)

    return send_from_directory(
        UPLOAD_FOLDER,
        row["stored_name"],
        as_attachment=True,
        download_name=row["original_name"]
    )


@app.route("/api/delete/<int:doc_id>", methods=["DELETE"])
@admin_required
def delete(doc_id):
    con = get_db()
    row = con.execute(
        "SELECT stored_name FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()

    if not row:
        con.close()
        return jsonify({"error": "Not found"}), 404

    path = os.path.join(UPLOAD_FOLDER, row["stored_name"])
    if os.path.exists(path):
        os.remove(path)

    con.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    con.commit()
    con.close()
    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    print("\n" + "="*45)
    print("  DocVault is running!")
    print("  Open: http://localhost:5000")
    print("  Database: docvault.db (local file)")
    print("="*45 + "\n")
    app.run(debug=True, port=5000)