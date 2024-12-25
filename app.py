from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
from markupsafe import Markup

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong secret key

ARTICLES_DIR = "articles"
if not os.path.exists(ARTICLES_DIR):
    os.makedirs(ARTICLES_DIR)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

def load_articles():
    articles = []
    if os.path.exists(ARTICLES_DIR):
        for filename in os.listdir(ARTICLES_DIR):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(ARTICLES_DIR, filename), "r") as file:
                        articles.append(json.load(file))
                except json.JSONDecodeError:
                    print(f"Error decoding {filename}")
    return sorted(articles, key=lambda x: x.get("date", ""), reverse=True)

@app.route('/')
def home():
    articles = load_articles()
    search_query = request.args.get('search', '').strip().lower()

    if search_query:
        articles = [
            article for article in articles
            if search_query in article['title'].lower() or search_query in article['content'].lower()
        ]

    page = int(request.args.get('page', 1))
    per_page = 6
    total_articles = len(articles)
    total_pages = (total_articles + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    paginated_articles = articles[start:end]

    return render_template(
        "home.html",
        articles=paginated_articles,
        total_pages=total_pages,
        current_page=page,
        search_query=search_query
    )

@app.template_filter('highlight')
def highlight(text, query):
    if not query or query.strip() == "":
        return text
    query = query.lower()
    highlighted = text.replace(query, f'<mark>{query}</mark>')
    return Markup(highlighted)


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
