from flask import Flask, request, redirect, session, render_template_string, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "lostfound_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lostfound.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20), default="user")

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500))
    item_type = db.Column(db.String(20))
    category = db.Column(db.String(100))
    image = db.Column(db.String(255))
    owner = db.Column(db.String(100))

def ai_category(text):
    text = text.lower()
    if "phone" in text or "laptop" in text:
        return "Electronics"
    if "wallet" in text:
        return "Wallet"
    if "bag" in text:
        return "Bag"
    if "key" in text:
        return "Keys"
    return "General"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(username="admin", password="admin123", role="admin"))
        db.session.commit()

@app.route("/")
def home():
    return render_template_string("""
    <h1>🔍 Lost & Found AI</h1>
    <p>College Project</p>
    <a href='/login'>Login</a> |
    <a href='/register'>Register</a>
    """)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        db.session.add(User(
            username=request.form["username"],
            password=request.form["password"],
            role="user"
        ))
        db.session.commit()
        return redirect("/login")
    return render_template_string("""
    <h2>Register</h2>
    <form method='post'>
    <input name='username' placeholder='Username'><br><br>
    <input name='password' type='password' placeholder='Password'><br><br>
    <button>Register</button>
    </form>
    """)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()
        if u:
            session["user"] = u.username
            session["role"] = u.role
            return redirect("/admin" if u.role=="admin" else "/dashboard")
    return render_template_string("""
    <h2>Login</h2>
    <form method='post'>
    <input name='username'><br><br>
    <input name='password' type='password'><br><br>
    <button>Login</button>
    </form>
    """)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    q = request.args.get("q","")
    if q:
        items = Item.query.filter(Item.title.contains(q)).all()
    else:
        items = Item.query.all()

    html = """
    <h2>User Dashboard</h2>
    <a href='/add'>Add Item</a> |
    <a href='/logout'>Logout</a>
    <form>
      <input name='q' placeholder='Search'>
      <button>Search</button>
    </form>
    """
    for i in items:
        html += f"<hr><b>{i.item_type.upper()}</b> - {i.title}<br>{i.description}<br>Category: {i.category}<br>"
    return html

@app.route("/add", methods=["GET","POST"])
def add():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        filename = ""
        f = request.files.get("image")
        if f and f.filename:
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.session.add(Item(
            title=request.form["title"],
            description=request.form["description"],
            item_type=request.form["item_type"],
            category=ai_category(request.form["title"]),
            image=filename,
            owner=session["user"]
        ))
        db.session.commit()
        return redirect("/dashboard")

    return render_template_string("""
    <h2>Add Lost/Found Item</h2>
    <form method='post' enctype='multipart/form-data'>
    <input name='title' placeholder='Item'><br><br>
    <input name='description' placeholder='Description'><br><br>
    <select name='item_type'>
      <option value='lost'>Lost</option>
      <option value='found'>Found</option>
    </select><br><br>
    <input type='file' name='image'><br><br>
    <button>Submit</button>
    </form>
    """)

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return "Access Denied"
    return f"<h2>Admin Panel</h2><p>Users: {User.query.count()}</p><p>Items: {Item.query.count()}</p>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
