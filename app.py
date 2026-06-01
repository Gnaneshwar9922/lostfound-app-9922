from flask import Flask, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename
import joblib

app = Flask(__name__)
app.secret_key = "lostfound_secret"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- ML LOAD ----------------
model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

def ai_classify(text):
    X = vectorizer.transform([text])
    return model.predict(X)[0]

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        name TEXT,
        desc TEXT,
        image TEXT,
        category TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    return """
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
    body{
        margin:0;
        font-family:Arial;
        background:#f2f2f2;
        padding-bottom:80px;
    }

    .header{
        background:#4CAF50;
        color:white;
        text-align:center;
        padding:15px;
        font-size:20px;
    }

    .card{
        background:white;
        margin:15px;
        padding:15px;
        border-radius:12px;
        text-align:center;
        box-shadow:0 3px 10px rgba(0,0,0,0.1);
    }

    .bottom{
        position:fixed;
        bottom:0;
        width:100%;
        display:flex;
        justify-content:space-around;
        background:white;
        padding:8px 0;
        border-top:1px solid #ddd;
    }

    .bottom a{
        text-align:center;
        font-size:12px;
        color:#4CAF50;
        text-decoration:none;
        display:flex;
        flex-direction:column;
        align-items:center;
        width:16%;
    }

    .bottom small{
        font-size:10px;
        color:#333;
    }
    </style>
    </head>

    <body>

    <div class="header">🔎 Smart Lost & Found AI System</div>

    <div class="card">👋 Welcome to Your AI Project</div>

    <div class="bottom">
        <a href="/">
            🏠<br><small>Home</small>
        </a>

        <a href="/lost">
            📦<br><small>Lost</small>
        </a>

        <a href="/found">
            🎁<br><small>Found</small>
        </a>

        <a href="/search">
            🔍<br><small>Search</small>
        </a>

        <a href="/admin">
            ⚙️<br><small>Admin</small>
        </a>

        <a href="/logout">
            🚪<br><small>Logout</small>
        </a>
    </div>

    </body>
    </html>
    """

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form["username"]
        return redirect("/")

    return """
    <h2>Login</h2>
    <form method="POST">
        <input name="username" placeholder="Username">
        <button>Login</button>
    </form>
    """

# ---------------- LOST ----------------
@app.route("/lost", methods=["GET", "POST"])
def lost():
    if request.method == "POST":
        name = request.form["name"]
        desc = request.form["desc"]
        img = request.files["image"]

        category = ai_classify(name + " " + desc)

        filename = secure_filename(img.filename)
        img.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = sqlite3.connect("data.db")
        c = conn.cursor()
        c.execute("""INSERT INTO items (type,name,desc,image,category)
                     VALUES (?,?,?,?,?)""",
                  ("lost", name, desc, filename, category))
        conn.commit()
        conn.close()

        return redirect("/")

    return """
    <h2>📦 Lost Item</h2>
    <form method="POST" enctype="multipart/form-data">
        <input name="name" placeholder="Item Name"><br><br>
        <input name="desc" placeholder="Description"><br><br>
        <input type="file" name="image"><br><br>
        <button>Submit</button>
    </form>
    """

# ---------------- FOUND ----------------
@app.route("/found", methods=["GET", "POST"])
def found():
    if request.method == "POST":
        name = request.form["name"]
        desc = request.form["desc"]
        img = request.files["image"]

        category = ai_classify(name + " " + desc)

        filename = secure_filename(img.filename)
        img.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = sqlite3.connect("data.db")
        c = conn.cursor()
        c.execute("""INSERT INTO items (type,name,desc,image,category)
                     VALUES (?,?,?,?,?)""",
                  ("found", name, desc, filename, category))
        conn.commit()
        conn.close()

        return redirect("/")

    return """
    <h2>🎁 Found Item</h2>
    <form method="POST" enctype="multipart/form-data">
        <input name="name" placeholder="Item Name"><br><br>
        <input name="desc" placeholder="Description"><br><br>
        <input type="file" name="image"><br><br>
        <button>Submit</button>
    </form>
    """

# ---------------- SEARCH ----------------
@app.route("/search", methods=["GET", "POST"])
def search():
    result = []
    matches = []

    if request.method == "POST":
        q = request.form["q"]

        conn = sqlite3.connect("data.db")
        c = conn.cursor()

        c.execute("SELECT * FROM items WHERE name LIKE ?", ('%' + q + '%',))
        result = c.fetchall()

        cat = ai_classify(q)
        c.execute("SELECT * FROM items WHERE category=?", (cat,))
        matches = c.fetchall()

        conn.close()

    html = """
    <h2>🔍 Smart Search</h2>

    <form method="POST">
        <input name="q" placeholder="Search item">
        <button>Search</button>
    </form>

    <h3>🤖 AI Matches</h3>
    """

    for r in matches:
        html += f"""
        <div style="border:1px solid #ddd;margin:10px;padding:10px">
        <b>{r[2]}</b><br>
        Category: {r[5]}<br>
        {r[3]}<br>
        <img src="/static/uploads/{r[4]}" width="120">
        </div>
        """

    html += "<h3>🔎 Exact Matches</h3>"

    for r in result:
        html += f"""
        <div style="border:1px solid #ddd;margin:10px;padding:10px">
        <b>{r[2]}</b><br>
        {r[3]}<br>
        <img src="/static/uploads/{r[4]}" width="120">
        </div>
        """

    return html

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("SELECT * FROM items")
    items = c.fetchall()
    conn.close()

    html = "<h2>⚙️ Admin Panel</h2>"

    for i in items:
        html += f"""
        <div style="border:1px solid #ddd;margin:10px;padding:10px">
        <b>{i[2]}</b> ({i[1]})<br>
        Category: {i[5]}<br>
        {i[3]}<br>
        <img src="/static/uploads/{i[4]}" width="100">
        </div>
        """

    return html

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)