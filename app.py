from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, send
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = "supersecretkey"

socketio = SocketIO(app)

# ----------------------------
# DATABASE SETUP
# ----------------------------

def init_db():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()

# ----------------------------
# PASSWORD HASH FUNCTION
# ----------------------------

def hash_password(password):

    return hashlib.sha256(password.encode()).hexdigest()


# ----------------------------
# LOGIN PAGE
# ----------------------------

@app.route("/", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])

def login():

    if request.method == "POST":

        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session["user"] = username
            return redirect("/chat")

    return render_template("login.html")


# ----------------------------
# REGISTER PAGE
# ----------------------------

@app.route("/register", methods=["GET","POST"])

def register():

    if request.method == "POST":

        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:

            cursor.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (username,password)
            )

            conn.commit()

        except:

            pass

        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ----------------------------
# CHAT PAGE
# ----------------------------

@app.route("/chat")

def chat():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT message FROM messages")

    history = cursor.fetchall()

    conn.close()

    return render_template("chat.html",user=session["user"],history=history)


# ----------------------------
# LOGOUT
# ----------------------------

@app.route("/logout")

def logout():

    session.pop("user",None)

    return redirect("/login")


# ----------------------------
# DOWNLOAD CHAT HISTORY
# ----------------------------

@app.route("/download")

def download_chat():

    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()

    cursor.execute("SELECT message FROM messages")

    data = cursor.fetchall()

    conn.close()

    text = ""

    for row in data:
        text += row[0] + "\n"

    return text,200,{
        "Content-Type":"text/plain",
        "Content-Disposition":"attachment; filename=chat_history.txt"
    }


# ----------------------------
# SOCKET CHAT
# ----------------------------

@socketio.on("message")

def handle_message(msg):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO messages(message) VALUES(?)",
        (msg,)
    )

    conn.commit()
    conn.close()

    send(msg,broadcast=True)


# ----------------------------
# RUN SERVER
# ----------------------------

if __name__ == "__main__":

    socketio.run(app,debug=True)