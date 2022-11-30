import random

from flask import Flask, abort, request
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from flask_migrate import Migrate

BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{BASE_DIR / 'main.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class QuoteModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(32), unique=False)
    text = db.Column(db.String(255), unique=False)
    rating = db.Column(db.Integer)

    def __init__(self, author, text, rating=1):
        self.author = author
        self.text = text
        self.rating = rating if 0 < rating < 6 else 1

    def __repr__(self):
        return f"Quote author: {self.author}, text: {self.text}"

    def to_dict(self):
        return {"id": self.id, "author": self.author, "text": self.text, "rating": self.rating}


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


@app.route("/quotes", methods=['POST'])
def post_quote():
    data = request.json
    # new_quote = QuoteModel(data["author"], data["text"])
    new_quote = QuoteModel(**data)
    db.session.add(new_quote)
    db.session.commit()
    return new_quote.to_dict()


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
    return f"Quote {quote_id} not found"


@app.route("/quotes/count")
def quotes_count():
    quotes_list = get_quotes()
    return f"Number of quotes: {len(quotes_list)}"


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
        filtered_list = [quote for quote in quotes_dict if quote["author"] in author and str(quote["rating"]) in rating]
    elif author:
        filtered_list = [quote for quote in quotes_dict if quote["author"] in author]
    elif rating:
        filtered_list = [quote for quote in quotes_dict if str(quote["rating"]) in rating]
    return filtered_list


if __name__ == "__main__":
    app.run(debug=True)
