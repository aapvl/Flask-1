import random
from flask import Flask, abort, request
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from flask_migrate import Migrate
from sqlalchemy.orm import validates, IntegrityError

BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'main.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.app_context().push()


class AuthorModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    surname = db.Column(db.String(32))
    quotes = db.relationship('QuoteModel', backref='author', lazy='dynamic', cascade="all, delete-orphan")

    # def __init__(self, name):
    #     self.name = name

    def to_dict(self):
        keys = AuthorModel.__table__.columns.keys()
        values = []
        for key in keys:
            values.append(getattr(self, key))
        result = dict(zip(keys, values))
        return result


class QuoteModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey(AuthorModel.id))
    text = db.Column(db.String(255), unique=False)
    rating = db.Column(db.Integer)

    def __init__(self, author, text, rating=1):
        self.author_id = author.id
        self.text = text
        self.rating = rating

    @validates("rating")
    def validate_rating(self, key, rating):
        if 0 < rating < 6:
            return rating
        return ValueError("rating must be [1, 5]")

    def __repr__(self):
        return f"Quote author: {self.author.to_dict}, text: {self.text}, rating: {self.rating}"

    def to_dict(self):
        keys = QuoteModel.__table__.columns.keys()
        values = []
        for key in keys:
            values.append(getattr(self, key))
        result = dict(zip(keys, values))
        del result["author_id"]
        result["author"] = self.author.name
        return result


# @app.errorhandler()
# TODO добавить обработчик 404

# def get_object_or_404(model, object_id):
#     obj = model.query.get(object_id)
#     if obj is None:
#         return f"Object with id = {object_id} not found", 404
#     return obj


# QUOTES handlers


@app.route("/quotes")
def get_quotes():
    quotes = QuoteModel.query.all()
    quotes_dict = []
    for quote in quotes:
        quotes_dict.append(quote.to_dict())
    return quotes_dict


@app.route("/quotes/<int:quote_id>")
def find_quote(quote_id):
    quote = QuoteModel.query.get(quote_id)
    if quote is not None:
        return quote.to_dict()
    return f"Quote {quote_id} not found", 404


@app.route("/authors/<int:author_id>/quotes")
def all_author_quotes(author_id):
    author = AuthorModel.query.get(author_id)
    if author is not None:
        quotes = author.quotes.all()
        quotes = [quote.to_dict() for quote in quotes]
        return quotes
    return f"Author with id {author_id} not found", 404


@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_quote(author_id):
    author = AuthorModel.query.get(author_id)
    new_quote = request.json
    if author is not None:
        q = QuoteModel(author, new_quote["text"])
        db.session.add(q)
        db.session.commit()
        return q.to_dict(), 201
    return f"Author with id {author_id} not found", 404


@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    new_data = request.json
    quote = QuoteModel.query.get(quote_id)
    if quote is not None:
        for key, value in new_data.items():
            setattr(quote, key, value)
            db.session.commit()
        return quote.to_dict()
    return f"Quote {quote_id} not found", 404


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete(quote_id):
    quote = QuoteModel.query.get(quote_id)
    if quote is not None:
        db.session.delete(quote)
        db.session.commit()
        return f"Quote {quote_id} deleted"
    return f"Quote {quote_id} not found", 404


@app.route("/quotes/count")
def quotes_count():
    return {"count": QuoteModel.query.count()}


@app.route("/quotes/random")
def get_random_quote():
    quotes = get_quotes()
    random_quote = quotes[random.randint(0, len(quotes)-1)]
    return random_quote


@app.route("/quotes/search", methods=["GET"])
def search_quotes():
    args = request.args
    author = args.get("author")
    rating = args.get("rating")
    quotes = QuoteModel.query.all()
    quotes_dict = []
    for quote in quotes:
        quotes_dict.append(quote.to_dict())
    if None not in (author, rating):
        filtered_list = [quote for quote in quotes_dict if str(quote["author"]) in author and str(quote["rating"]) in rating]
    elif author:
        filtered_list = [quote for quote in quotes_dict if str(quote["author"]) in author]
    elif rating:
        filtered_list = [quote for quote in quotes_dict if str(quote["rating"]) in rating]
    return filtered_list


# AUTHORS handlers


@app.route("/authors")
def get_all_authors():
    authors = AuthorModel.query.all()
    authors_dict = []
    for author in authors:
        authors_dict.append(author.to_dict())
    return authors_dict


@app.route("/authors/<int:author_id>")
def get_author(author_id):
    author = AuthorModel.query.get(author_id)
    return author.to_dict()


@app.route("/authors", methods=["POST"])
def create_author():
    author_data = request.json
    author = AuthorModel(**author_data)
    db.session.add(author)
    db.session.commit()
    return author.to_dict(), 201


@app.route("/authors/<int:author_id>", methods=["PUT"])
def update_author(author_id):
    data = request.json
    author = AuthorModel.query.get(author_id)
    if author is not None:
        for key, value in data.items():
            setattr(author, key, value)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return f"Author name must be unique", 400
        return author.to_dict()
    return f"Author with id {author_id} not found", 404


@app.route("/authors/<int:author_id>", methods=["DELETE"])
def delete_author(author_id):
    author = AuthorModel.query.get(author_id)
    if author is not None:
        db.session.delete(author)
        db.session.commit()
        return f"Author with id {author_id} deleted"
    return f"Author with id {author_id} not found", 404


if __name__ == "__main__":
    app.run(debug=True)
