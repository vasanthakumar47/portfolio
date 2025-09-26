import os, json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

APP_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_PATH = os.path.join(APP_DIR, "data.json")
UPLOAD_FOLDER = os.path.join(APP_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "vasanth")
# If ADMIN_PASSWORD_HASH not set, we derive hash from ADMIN_PASSWORD (dev only)
_admin_pw_hash_env = os.getenv("ADMIN_PASSWORD_HASH")
_admin_pw_plain = os.getenv("ADMIN_PASSWORD")  # dev convenience
if _admin_pw_hash_env:
    ADMIN_PASSWORD_HASH = _admin_pw_hash_env
else:
    # fallback for local/dev
    ADMIN_PASSWORD_HASH = generate_password_hash(_admin_pw_plain or "vasanthksrym")

DEFAULT_BIO = {
    "name": "Vasantha Kumar",
    "title": "Data Engineer | Python Developer",
    "location": "Chennai, India",
    "email": "vasanthakumar28042001@gmail.com",
    "phone": "+91-7200551725",
    "about": "Short intro about you. Passionate about Flask, Data, and Automation.",
    "skills": ["Python", "Flask", "Pandas", "MySQL", "HTML/CSS", "JavaScript"],
    "projects": [
        {"name": "Project One", "desc": "Your role and impact.", "link": "https://example.com"},
        {"name": "Project Two", "desc": "Quick highlight.", "link": "https://example.com"}
    ],
    "photo": ""
}

def load_bio():
    if not os.path.exists(DATA_PATH):
        return DEFAULT_BIO.copy()
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return DEFAULT_BIO.copy()

def save_bio(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Auth helper ---
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user") != ADMIN_USERNAME:
            flash("Please login to edit your bio.", "danger")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def home():
    bio = load_bio()
    return render_template("index.html", bio=bio)

@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    bio = load_bio()
    if request.method == "POST":
        bio["name"] = request.form.get("name", "").strip()
        bio["title"] = request.form.get("title", "").strip()
        bio["location"] = request.form.get("location", "").strip()
        bio["email"] = request.form.get("email", "").strip()
        bio["phone"] = request.form.get("phone", "").strip()
        bio["about"] = request.form.get("about", "").strip()

        skills_raw = request.form.get("skills", "").strip()
        bio["skills"] = [s.strip() for s in skills_raw.split(",") if s.strip()]

        proj_names = request.form.getlist("project_name")
        proj_descs = request.form.getlist("project_desc")
        proj_links = request.form.getlist("project_link")
        projects = []
        for n, d, l in zip(proj_names, proj_descs, proj_links):
            if n.strip() or d.strip() or l.strip():
                projects.append({"name": n.strip(), "desc": d.strip(), "link": l.strip()})
        bio["projects"] = projects

        file = request.files.get("photo")
        if file and file.filename:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(save_path)
                bio["photo"] = f"uploads/{filename}"
                flash("Profile photo updated.", "success")
            else:
                flash("Invalid image type. Allowed: png, jpg, jpeg, gif, webp", "danger")

        save_bio(bio)
        flash("Bio saved successfully!", "success")
        return redirect(url_for("home"))

    skills_text = ", ".join(bio.get("skills", []))
    return render_template("edit.html", bio=bio, skills_text=skills_text)

# --- Auth routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["user"] = ADMIN_USERNAME
            flash("Logged in successfully!", "success")
            next_url = request.args.get("next") or url_for("home")
            return redirect(next_url)
        flash("Invalid credentials.", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "success")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
