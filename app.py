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
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Lost & Found App</title>

    <!-- Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

    <style>
        body {
            margin: 0;
            font-family: Arial;
            background: linear-gradient(135deg, #4facfe, #00f2fe);
            color: white;
            text-align: center;
        }

        .container {
            padding-top: 80px;
        }

        h1 {
            font-size: 40px;
        }

        p {
            font-size: 18px;
        }

        .btn {
            display: inline-block;
            margin: 10px;
            padding: 15px 25px;
            border-radius: 10px;
            text-decoration: none;
            color: white;
            background: rgba(0,0,0,0.3);
            font-size: 18px;
            transition: 0.3s;
        }

        .btn:hover {
            background: rgba(0,0,0,0.6);
        }

        .icons {
            margin-top: 40px;
            font-size: 40px;
        }

        .nav {
            position: fixed;
            bottom: 0;
            width: 100%;
            background: rgba(0,0,0,0.5);
            padding: 10px;
        }

        .nav i {
            margin: 0 20px;
            font-size: 22px;
        }
    </style>
</head>

<body>

<div class="container">
    <h1>🔍 Lost & Found AI System</h1>
    <p>Find your lost items or report found items easily</p>

    <a class="btn" href="/login"><i class="fa fa-user"></i> Login</a>
    <a class="btn" href="/register"><i class="fa fa-user-plus"></i> Register</a>

    <div class="icons">
        <i class="fa fa-search"></i>
        <i class="fa fa-box"></i>
        <i class="fa fa-shield"></i>
    </div>
</div>

<!-- Bottom Navigation -->
<div class="nav">
    <i class="fa fa-home"></i>
    <i class="fa fa-search"></i>
    <i class="fa fa-user"></i>
    <i class="fa fa-cog"></i>
</div>

</body>
</html>
""")


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
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

    <style>
        body {
            margin: 0;
            font-family: Arial;
            background: linear-gradient(135deg, #141e30, #243b55);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        .card {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            width: 300px;
            text-align: center;
        }

        input {
            width: 90%;
            padding: 10px;
            margin: 10px 0;
            border-radius: 8px;
            border: none;
        }

        button {
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 8px;
            background: #00c6ff;
            color: white;
            font-size: 16px;
            cursor: pointer;
        }

        button:hover {
            background: #0072ff;
        }

        a {
            color: #00c6ff;
            text-decoration: none;
        }
    </style>
</head>

<body>

<div class="card">
    <h2><i class="fa fa-user"></i> Login</h2>

    <form method="POST">
        <input name="username" placeholder="Username" required><br>
        <input name="password" type="password" placeholder="Password" required><br>
        <button type="submit">Login</button>
    </form>

    <p>New user? <a href="/register">Register</a></p>
</div>

</body>
</html>
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
