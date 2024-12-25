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

if __name__ == "__main__":
    app.run(debug=True)
