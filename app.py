from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secret123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db = SQLAlchemy(app)

# ---------------- DATABASE MODEL ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))  # "user" or "admin"

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user" in session:
        return f"Welcome {session['user']} ({session['role']})"
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
            <input name="username" placeholder="Username"><br>
            <input name="password" type="password" placeholder="Password"><br>
            <button type="submit">Register</button>
        </form>
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

        return "Invalid Login"

    return render_template_string("""
        <h2>Login</h2>
        <form method="POST">
            <input name="username"><br>
            <input name="password" type="password"><br>
            <button type="submit">Login</button>
        </form>
    """)

# ---------------- USER DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return f"User Dashboard - Welcome {session['user']}"

# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin():
    if "user" not in session or session["role"] != "admin":
        return "Access Denied"
    return "Admin Panel - Full Control"

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- INIT DB ----------------
@app.before_first_request
def create_tables():
    db.create_all()

    # create default admin
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(username="admin", password="admin123", role="admin")
        db.session.add(admin)
        db.session.commit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
