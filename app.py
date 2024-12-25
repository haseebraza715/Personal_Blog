from flask import Flask, render_template, request, redirect, url_for
import os
import json

app = Flask(__name__)

ARTICLES_DIR = "articles"

if not os.path.exists(ARTICLES_DIR):
    os.makedirs(ARTICLES_DIR)

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
    filepath = os.path.join(ARTICLES_DIR, f"{title}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            article = json.load(file)
        return render_template("article.html", article=article)
    else:
        return "Article not found", 404
    
@app.route('/admin')
def admin_dashboard():
    articles = load_articles()
    return render_template("admin_dashboard.html", articles=articles)


@app.route('/admin/new', methods=["GET", "POST"])
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
def delete_article(title):
    filepath = os.path.join(ARTICLES_DIR, f"{title.replace(' ', '_')}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('admin_dashboard'))



if __name__ == "__main__":
    app.run(debug=True)
