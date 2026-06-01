from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "lostfound_secret_key"

# ---------------- DATABASE ----------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lostfound.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- USER TABLE ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))  # admin / user


# ---------------- LOST FOUND TABLE ----------------
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500))
    type = db.Column(db.String(20))  # lost / found
    owner = db.Column(db.String(100))


# ---------------- INIT DB (FIX FOR RENDER) ----------------
with app.app_context():
    db.create_all()

    # create admin if not exists
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(username="admin", password="admin123", role="admin")
        db.session.add(admin)
        db.session.commit()


# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=request.form["password"],
            role="user"
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template_string("""
        <h2>Register</h2>
        <form method="POST">
            <input name="username" placeholder="Username" required><br>
            <input name="password" type="password" placeholder="Password" required><br>
            <button type="submit">Register</button>
        </form>
        <a href="/login">Login</a>
    """)


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()

        if user:
            session["user"] = user.username
            session["role"] = user.role

            if user.role == "admin":
                return redirect("/admin")
            else:
                return redirect("/dashboard")

        return "Invalid login"

    return render_template_string("""
        <h2>Login</h2>
        <form method="POST">
            <input name="username" required><br>
            <input name="password" type="password" required><br>
            <button type="submit">Login</button>
        </form>
        <a href="/register">Register</a>
    """)


# ---------------- USER DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    items = Item.query.all()

    return render_template_string("""
        <h2>User Dashboard</h2>
        <p>Welcome {{user}}</p>

        <a href="/add">Add Lost/Found Item</a> |
        <a href="/logout">Logout</a>

        <h3>Items</h3>
        {% for i in items %}
            <p><b>{{i.type}}</b> - {{i.title}} : {{i.description}}</p>
        {% endfor %}
    """, user=session["user"], items=items)


# ---------------- ADD ITEM ----------------
@app.route("/add", methods=["GET", "POST"])
def add():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        item = Item(
            title=request.form["title"],
            description=request.form["description"],
            type=request.form["type"],
            owner=session["user"]
        )
        db.session.add(item)
        db.session.commit()
        return redirect("/dashboard")

    return render_template_string("""
        <h2>Add Item</h2>
        <form method="POST">
            <input name="title" placeholder="Item name"><br>
            <input name="description" placeholder="Description"><br>
            <select name="type">
                <option value="lost">Lost</option>
                <option value="found">Found</option>
            </select><br>
            <button type="submit">Submit</button>
        </form>
    """)


# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin():
    if "user" not in session or session["role"] != "admin":
        return "Access Denied"

    users = User.query.all()
    items = Item.query.all()

    return render_template_string("""
        <h2>Admin Panel</h2>
        <p>Welcome Admin</p>

        <h3>Users</h3>
        {% for u in users %}
            <p>{{u.username}} - {{u.role}}</p>
        {% endfor %}

        <h3>All Items</h3>
        {% for i in items %}
            <p>{{i.type}} - {{i.title}}</p>
        {% endfor %}

        <a href="/logout">Logout</a>
    """, users=users, items=items)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)