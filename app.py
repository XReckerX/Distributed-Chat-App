import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chat.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# In-memory mapping: username -> set of Socket.IO session IDs.
online_users = {}


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("chat.html", username=session["username"])


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        conn = db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["username"] = username
            return redirect(url_for("index"))
        error = "Invalid username or password."
    return render_template("login.html", mode="login", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if len(username) < 3 or len(username) > 20:
            error = "Username must be 3–20 characters."
        elif not username.replace("_", "").isalnum():
            error = "Use only letters, numbers, and underscore."
        elif len(password) < 4:
            error = "Password must be at least 4 characters."
        else:
            conn = db()
            try:
                conn.execute(
                    "INSERT INTO users(username, password_hash, created_at) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), now_iso())
                )
                conn.commit()
                session["username"] = username
                return redirect(url_for("index"))
            except sqlite3.IntegrityError:
                error = "Username already exists."
            finally:
                conn.close()

    return render_template("login.html", mode="register", error=error)


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/api/history")
@login_required
def history():
    conn = db()
    rows = conn.execute("""
        SELECT sender, recipient, body, created_at
        FROM messages
        WHERE recipient IS NULL
           OR sender = ?
           OR recipient = ?
        ORDER BY id DESC
        LIMIT 100
    """, (session["username"], session["username"])).fetchall()
    conn.close()

    return jsonify([dict(row) for row in reversed(rows)])


def broadcast_online_users():
    socketio.emit("online_users", sorted(online_users.keys()))


@socketio.on("connect")
def handle_connect():
    username = session.get("username")
    if not username:
        return False

    online_users.setdefault(username, set()).add(request.sid)
    join_room(username)
    broadcast_online_users()
    emit("system_message", {
        "text": f"Welcome, {username}! You are connected to the distributed chat server."
    })


@socketio.on("disconnect")
def handle_disconnect():
    username = session.get("username")
    if not username:
        return

    sockets = online_users.get(username, set())
    sockets.discard(request.sid)

    if not sockets:
        online_users.pop(username, None)
        broadcast_online_users()


@socketio.on("send_message")
def handle_message(data):
    username = session.get("username")
    if not username:
        emit("error_message", {"text": "You are not authenticated."})
        return

    body = str(data.get("body", "")).strip()
    recipient = data.get("recipient")
    recipient = str(recipient).strip() if recipient else None

    if not body:
        emit("error_message", {"text": "Message cannot be empty."})
        return
    if len(body) > 2000:
        emit("error_message", {"text": "Message is too long."})
        return

    # Private messages are addressed to a username room.
    # Broadcast messages use recipient = None.
    created = now_iso()

    conn = db()
    conn.execute(
        "INSERT INTO messages(sender, recipient, body, created_at) VALUES (?, ?, ?, ?)",
        (username, recipient, body, created)
    )
    conn.commit()
    conn.close()

    payload = {
        "sender": username,
        "recipient": recipient,
        "body": body,
        "created_at": created
    }

    if recipient:
        emit("new_message", payload, room=username)
        if recipient != username:
            emit("new_message", payload, room=recipient)
    else:
        socketio.emit("new_message", payload)


if __name__ == "__main__":
    init_db()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    print(f"Distributed Chat Server running at http://127.0.0.1:{port}")
    print(f"LAN access: http://<YOUR-PC-IP>:{port}")
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True)
