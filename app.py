from flask import Flask, render_template, request, redirect, url_for, session
import os
import json

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong secret key

# Directory for storing articles
ARTICLES_DIR = "articles"
if not os.path.exists(ARTICLES_DIR):
    os.makedirs(ARTICLES_DIR)

# Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

# Helper function to load articles
def load_articles():
    articles = []
    for filename in os.listdir(ARTICLES_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(ARTICLES_DIR, filename), "r") as file:
                articles.append(json.load(file))
    return sorted(articles, key=lambda x: x["date"], reverse=True)

@app.route('/')
def home():
    articles = load_articles()
    return render_template("home.html", articles=articles)

@app.route('/article/<title>')
def article(title):
    filepath = os.path.join(ARTICLES_DIR, f"{title.replace(' ', '_')}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            article = json.load(file)
        return render_template("article.html", article=article)
    else:
        return "Article not found", 404

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            return "Invalid credentials", 401
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("home"))

def admin_required(func):
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__  # Avoid Flask routing issues
    return wrapper

@app.route('/admin')
@admin_required
def admin_dashboard():
    articles = load_articles()
    return render_template("admin_dashboard.html", articles=articles)

@app.route('/admin/new', methods=["GET", "POST"])
@admin_required
def new_article():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        date = request.form["date"]

        # Save article as JSON file
        filename = f"{title.replace(' ', '_')}.json"
        filepath = os.path.join(ARTICLES_DIR, filename)
        with open(filepath, "w") as file:
            json.dump({"title": title, "content": content, "date": date}, file)

        return redirect(url_for('admin_dashboard'))
    return render_template("new_article.html")

@app.route('/admin/edit/<title>', methods=["GET", "POST"])
@admin_required
def edit_article(title):
    filepath = os.path.join(ARTICLES_DIR, f"{title.replace(' ', '_')}.json")
    if not os.path.exists(filepath):
        return "Article not found", 404

    if request.method == "POST":
        new_title = request.form["title"]
        content = request.form["content"]
        date = request.form["date"]

        # Update article file
        new_filepath = os.path.join(ARTICLES_DIR, f"{new_title.replace(' ', '_')}.json")
        with open(new_filepath, "w") as file:
            json.dump({"title": new_title, "content": content, "date": date}, file)

        # If title changes, delete the old file
        if filepath != new_filepath:
            os.remove(filepath)

        return redirect(url_for('admin_dashboard'))

    # Load article data for editing
    with open(filepath, "r") as file:
        article = json.load(file)

    return render_template("edit_article.html", article=article)

@app.route('/admin/delete/<title>', methods=["POST"])
@admin_required
def delete_article(title):
    filepath = os.path.join(ARTICLES_DIR, f"{title.replace(' ', '_')}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('admin_dashboard'))

if __name__ == "__main__":
    app.run(debug=True)
