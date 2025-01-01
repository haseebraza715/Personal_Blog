from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
from markupsafe import Markup

app = Flask(__name__)

COMMENTS_DIR = "comments"
if not os.path.exists(COMMENTS_DIR):
    os.makedirs(COMMENTS_DIR)

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
    featured_articles = [article for article in articles if article.get('featured', False)]

    search_query = request.args.get('search', '').strip().lower()
    selected_tag = request.args.get('tag', '')

    if search_query:
        articles = [
            article for article in articles
            if search_query in article['title'].lower() or search_query in article['content'].lower()
        ]

    if selected_tag:
        articles = [article for article in articles if selected_tag in article.get('tags', [])]

    page = int(request.args.get('page', 1))  
    per_page = 6 
    total_articles = len(articles)
    total_pages = (total_articles + per_page - 1) // per_page 

    start = (page - 1) * per_page
    end = start + per_page
    paginated_articles = articles[start:end]

    all_tags = sorted(set(tag for article in articles for tag in article.get('tags', [])))

    return render_template(
        "home.html",
        featured_articles=featured_articles,
        articles=paginated_articles,
        total_pages=total_pages,
        current_page=page,
        search_query=search_query,
        selected_tag=selected_tag,
        all_tags=all_tags
    )

@app.template_filter('highlight')
def highlight(text, query):
    if not query or query.strip() == "":
        return text
    query = query.lower()
    highlighted = text.replace(query, f'<mark>{query}</mark>')
    return Markup(highlighted)
@app.route('/login', methods=["GET", "POST"])
def login():
    users_file = "users.json"
    error = None  

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if os.path.exists(users_file):
            with open(users_file, "r") as file:
                users = json.load(file)

            if username in users and users[username] == password:
                session["logged_in"] = True
                session["username"] = username  
                return redirect(url_for("admin_dashboard"))
            else:
                error = "Invalid username or password" 
        else:
            error = "No registered users found"

    return render_template("login.html", error=error)


@app.route('/logout')
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("home"))

def admin_required(func):
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__  
    return wrapper
@app.route('/admin')
@admin_required
def admin_dashboard():
    articles = load_articles()  
    total_articles = len(articles)

    tag_counts = {}
    for article in articles:
        for tag in article.get('tags', []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    page = int(request.args.get('page', 1))  
    per_page = 5  
    total_pages = (total_articles + per_page - 1) // per_page  
    start = (page - 1) * per_page
    paginated_articles = articles[start:start + per_page]

    return render_template(
        "admin_dashboard.html",
        articles=paginated_articles,
        total_articles=total_articles,
        tag_counts=tag_counts,
        total_pages=total_pages,
        current_page=page
    )


@app.route('/admin/new', methods=["GET", "POST"])
@admin_required
def new_article():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        date = request.form.get("date", "").strip()
        tags = request.form.get("tags", "").split(",")
        tags = [tag.strip() for tag in tags if tag.strip()]
        featured = "featured" in request.form

        if not title or not content or not date:
            return render_template("new_article.html", error="Title, content, and date are required.")

        from werkzeug.utils import secure_filename
        filename = secure_filename(f"{title}.json")
        filepath = os.path.join(ARTICLES_DIR, filename)

        if os.path.exists(filepath):
            return render_template("new_article.html", error="An article with this title already exists.")

        try:
            with open(filepath, "w") as file:
                json.dump(
                    {"title": title, "content": content, "date": date, "tags": tags, "featured": featured},
                    file,
                )
        except IOError:
            return render_template("new_article.html", error="Failed to save the article. Please try again.")

        return redirect(url_for("admin_dashboard"))

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
        tags = request.form["tags"].split(",")
        tags = [tag.strip() for tag in tags if tag.strip()]
        featured = "featured" in request.form

        new_filepath = os.path.join(ARTICLES_DIR, f"{new_title.replace(' ', '_')}.json")
        with open(new_filepath, "w") as file:
            json.dump({"title": new_title, "content": content, "date": date, "tags": tags, "featured": featured}, file)

        if filepath != new_filepath:
            os.remove(filepath)

        return redirect(url_for('admin_dashboard'))

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

@app.route('/article/<title>')
def view_article(title):
    filepath = os.path.join(ARTICLES_DIR, f"{title.replace(' ', '_')}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            article = json.load(file)

        comments_file = os.path.join(COMMENTS_DIR, f"{title.replace(' ', '_')}_comments.json")
        if os.path.exists(comments_file):
            with open(comments_file, "r") as file:
                comments = json.load(file)
        else:
            comments = []

        all_articles = load_articles()
        related_articles = [
            a for a in all_articles
            if a != article and set(a.get("tags", [])).intersection(article.get("tags", []))
        ][:3]

        return render_template("article.html", article=article, comments=comments, related_articles=related_articles)
    else:
        return "Article not found", 404

@app.route('/article/<title>/add_comment', methods=["POST"])
def add_comment(title):
    comment = request.form["comment"]

    comments_file = os.path.join(COMMENTS_DIR, f"{title.replace(' ', '_')}_comments.json")
    if not os.path.exists(comments_file):
        with open(comments_file, "w") as file:
            json.dump([], file)

    with open(comments_file, "r+") as file:
        comments = json.load(file)
        comments.append(comment)
        file.seek(0)
        json.dump(comments, file)

    return redirect(url_for("view_article", title=title))
@app.route('/admin/toggle_featured/<title>', methods=["POST"])
@admin_required
def toggle_featured(title):
    filepath = os.path.join(ARTICLES_DIR, f"{title.replace(' ', '_')}.json")
    
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            article = json.load(file)  

        article['featured'] = not article.get('featured', False)

        with open(filepath, "w") as file:
            json.dump(article, file) 
        
        print(f"Article '{title}' updated. Featured status: {article['featured']}")
    else:
        print(f"Error: Article file '{title}' not found!")

    return redirect(url_for('admin_dashboard'))


@app.route('/register', methods=["GET", "POST"])
def register():
    users_file = "users.json"

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not os.path.exists(users_file):
            with open(users_file, "w") as file:
                json.dump({}, file)

        with open(users_file, "r+") as file:
            users = json.load(file)
            if username in users:
                return "Username already exists", 400

            users[username] = password
            file.seek(0)
            json.dump(users, file)

        return redirect(url_for("login"))

    return render_template("register.html")




if __name__ == "__main__":
    app.run(debug=True)
