from flask import Flask, request, g
import random
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "test.db"
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def quote_to_dict(values):
    keys = ["id", "author", "text"]
    result_quote = dict(zip(keys, values))
    return result_quote


@app.route("/quotes")
def get_quotes():
    select_quotes = "SELECT * from quotes"
    cursor = get_db().cursor()
    cursor.execute(select_quotes)
    values = cursor.fetchall()
    quotes = []
    for value in values:
        quote = quote_to_dict(value)
        quotes.append(quote)
    return quotes


def find_quote_db(quote_id):
    select_quote = f"SELECT * FROM quotes WHERE id = {quote_id};"
    cursor = get_db().cursor()
    cursor.execute(select_quote)
    value = cursor.fetchone()
    return value


@app.route("/quotes/<int:quote_id>")
def find_quote(quote_id):
    select_quote = find_quote_db(quote_id)
    if select_quote is not None:
        return quote_to_dict(select_quote)
    else:
        return f"Quote {quote_id} not found", 404


@app.route("/quotes/count")
def quotes_count():
    select_quotes = f"SELECT * FROM quotes"
    cursor = get_db().cursor()
    cursor.execute(select_quotes)
    quotes_num = cursor.fetchall()
    return f"Number of quotes: {len(quotes_num)}"


@app.route("/quotes/random")
def get_random_quote():
    all_quotes = get_quotes()
    random_quote = all_quotes[random.randint(0, len(all_quotes)-1)]
    return random_quote


@app.route("/quotes", methods=['POST'])
def post_quote():
    data = request.json
    create_quote = "INSERT INTO quotes (author,text) VALUES (?, ?)"
    connect = get_db()
    cursor = connect.cursor()
    cursor.execute(create_quote, (data["author"], data["text"]))
    connect.commit()
    data["id"] = cursor.lastrowid
    return data, 201


@app.route("/quotes/<int:quote_id>", methods=['PUT'])
def edit_quote(quote_id):
    new_data = request.json
    update_quote = """
    UPDATE quotes
    SET author = ?, text = ?
    WHERE id = ?;
    """
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(update_quote, (*new_data, quote_id))
    connection.commit()
    if cursor.rowcount > 0:
        return f"Quote {quote_id} updated"
    return f"Quote {quote_id} not found"


@app.route("/quotes/<int:quote_id>", methods=['DELETE'])
def delete(quote_id):
    delete_quote = "DELETE FROM quotes WHERE id = ?;"
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute(delete_quote, (quote_id, ))
    connection.commit()
    if cursor.rowcount > 0:
        return f"Quote {quote_id} deleted"
    return f"Quote {quote_id} not found"


# @app.route("/quotes/search", methods=["GET"])
# def search_quotes():
#     args = request.args
#     author = args.get("author")
#     rating = args.get("rating")
#     if None not in (author, rating):
#         result = [quote for quote in quotes if quote["author"] in author and str(quote["rating"]) in rating]
#     elif author:
#         result = [quote for quote in quotes if quote["author"] in author]
#     elif rating:
#         result = [quote for quote in quotes if str(quote["rating"]) in rating]
#     return result


if __name__ == "__main__":
    app.run(debug=True)
