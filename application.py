import os

<<<<<<< HEAD
from flask import Flask, session, request, flash, jsonify, redirect, render_template, url_for, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from datetime import datetime
import requests
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
=======
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
>>>>>>> 48a033c87744585695edfe9d4d5986930a0931fd
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

<<<<<<< HEAD
# Just a setting so our api returns json in the order we specified
app.config["JSON_SORT_KEYS"] = False

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

api_key = "UuPi12vgevoTBA1dDCs3jA"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("You must log in to view that page!", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    # If user is searching for a book
    if request.method == "POST":
        
        query = request.form.get("query")
        # If the query is blank
        if not query:
            flash("You need to enter search!", "warning")
            return redirect(url_for("index"))

        # Search for the book by isbn, title or author in the db
        results = db.execute("SELECT * FROM books\
            WHERE isbn ILIKE '%'||:q||'%'\
            OR title ILIKE '%'||:q||'%'\
            OR author ILIKE '%'||:q||'%'\
            ORDER BY title", 
            {"q":query}).fetchall()

        # If no results are found
        if not len(results):
            flash("No results found!", "info")
            return redirect(url_for("index"))
        
        # Display the results
        return render_template("index.html", results=results)
    
    return render_template("index.html")


@app.route("/book/<int:book_id>", methods=["GET", "POST"])
@login_required
def book(book_id):

    # If a review is being submitted
    if request.method == "POST":

        # Get the values form the form
        review = request.form.get("review")
        rating = request.form.get("rating")
        user_id = session["user_id"]
        date = datetime.now()

        # Checking if the form is correct
        if not review or not rating:
            flash("Please fill out both rating and review!", "warning")
            return redirect(url_for("book", book_id=book_id))

        if len(review) > 1024:
            flash("Your review is too long, maximum number of characters is 1024!", "warning")
            return redirect(url_for("book", book_id=book_id))

        # Checking if the user already submitted a review for that book
        check = db.execute("SELECT id FROM reviews\
            WHERE user_id=:user_id\
            AND book_id=:book_id", 
            {"user_id": user_id, "book_id": book_id}).first()

        if check:
            flash("You may submit only one review per book!", "warning")
            return redirect(url_for("book", book_id=book_id))

        # Inject the review in the database
        db.execute("INSERT INTO reviews\
            (user_id, book_id, review, rating, date)\
            VALUES(:user_id, :book_id, :review, :rating, :date)",
            { "user_id": user_id, "book_id": book_id, 
            "review": review, "rating": rating, "date": date})
        
        db.commit()

        return redirect(url_for("book", book_id=book_id))
    
    # Get the values we need for the page
    book = db.execute("SELECT * FROM books\
        WHERE id=:book_id",
        {"book_id": book_id}).first()
    
    reviews = db.execute("SELECT reviews.review, reviews.date, reviews.rating, users.username\
        FROM reviews\
        JOIN users ON reviews.user_id = users.id\
        WHERE book_id=:book_id",
        {"book_id": book_id}).fetchall()

    # Get the values from Goodreads API
    res = requests.get(
        "https://www.goodreads.com/book/review_counts.json",
        params={"key": api_key, "isbns": book["isbn"]}
    )

    gr_book = res.json()["books"][0]
    
    # And store them in a dict
    gr_ratings = {
        "work_ratings_count" : format(gr_book.get("work_ratings_count"),','),
        "average_rating" : gr_book.get("average_rating")
    }

    return render_template("book.html", book=book, reviews=reviews, gr_ratings=gr_ratings)
    
@app.route("/api/<isbn>")
def api(isbn):
    
    # Find the book by the isbn
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).first()

    if not book:
        abort(404)

    # Get the values we need and put them in a dict
    review_count = db.execute("SELECT COUNT(*) FROM reviews WHERE book_id=:book_id", {"book_id": book["id"]}).first()
    average_rating = db.execute("SELECT CAST(AVG(rating) AS DECIMAL(10, 2)) FROM reviews WHERE book_id=:book_id", {"book_id": book["id"]}).first()
    
    api_book = {
        "title": book["title"],
        "author": book["author"],
        "year": book["year"],
        "isbn": book["isbn"],
        "review_count": review_count[0],
        "average_rating": "Not rated yet" if average_rating[0] == None else float(average_rating[0])
    }

    # Return them as json
    return jsonify(api_book)
=======
# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    shares = db.execute("SELECT shares, SUM(num_of_shares) FROM purchases JOIN users ON purchases.user_id=users.id WHERE users.id = :session_id GROUP BY purchases.shares", session_id = session["user_id"])

    share_list = []

    total = 0

    for row in shares:

        list_row = {}
        x = row["shares"]
        share = lookup(x)["symbol"]
        share_name = lookup(x)["name"]
        share_price = lookup(x)["price"]
        owned_shares = db.execute("SELECT SUM(num_of_shares) FROM purchases JOIN users ON purchases.user_id=users.id WHERE users.id = :session_id AND purchases.shares = :share", session_id = session["user_id"], share = x)[0]["SUM(num_of_shares)"]
        owned_value = owned_shares*share_price

        total += owned_value

        list_row["share"] = share
        list_row["share_name"] = share_name
        list_row["share_price"] = round(share_price, 2)
        list_row["owned_shares"] = owned_shares
        list_row["owned_value"] = round(owned_value, 2)

        if owned_shares != 0:

            share_list.append(list_row)

    users_credit = round((db.execute("SELECT cash FROM users WHERE id = :session_id", session_id = session["user_id"])[0]["cash"]), 2)
    return render_template("index.html", rows = share_list, cash = users_credit, total = round(total, 2))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        symbol = lookup(request.form.get("symbol"))["symbol"]

        share_n = request.form.get("shares", type=int)

        rows = lookup(symbol)

        if share_n < 0 or not share_n:

            return apology("please provide a positive number", 403)

        if not symbol:

            return apology("please provide a valid share symbol", 403)

        users_credit = float(db.execute("SELECT cash FROM users WHERE id = :session_id", session_id = session["user_id"])[0]["cash"])

        share_price = lookup(symbol)["price"]

        total_price = round(share_price * share_n, 2)

        if users_credit < total_price:

            return apology("Insufficient funds", 403)

        else:

            db.execute("UPDATE users SET cash= :cash WHERE id= :session_id", cash= users_credit - total_price, session_id = session["user_id"])

            db.execute("INSERT INTO purchases (user_id, shares, num_of_shares, at_price, time) VALUES(:session_id, :symbol, :share_n, :share_price, CURRENT_TIMESTAMP)", session_id = session["user_id"], symbol = symbol, share_n = share_n, share_price = share_price)



        return render_template("buy.html", rows = rows)
    else:
        return render_template("buy.html", rows = None)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    shares = db.execute("SELECT shares, num_of_shares, at_price, time FROM purchases JOIN users ON purchases.user_id=users.id WHERE users.id = :session_id", session_id = session["user_id"])

    return render_template("history.html", rows = shares)

>>>>>>> 48a033c87744585695edfe9d4d5986930a0931fd


@app.route("/login", methods=["GET", "POST"])
def login():
<<<<<<< HEAD

    # Forget the user
    session.pop("user_id", None)
=======
    """Log user in"""

    # Forget any user_id
    session.clear()
>>>>>>> 48a033c87744585695edfe9d4d5986930a0931fd

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
<<<<<<< HEAD
            flash("You must provide a username!", "danger")
            return redirect(url_for("login"))
        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("You must provide a password!", "danger")
            return redirect(url_for("login"))

        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for user
        user_query = db.execute(
            "SELECT * FROM users WHERE username = :username",
            {"username": username}
        ).first()

        # Ensure username exists and the password is correct
        if not user_query or not check_password_hash(user_query["password"], password):

            flash("Invalid username and/or password!", "danger")
            return redirect(url_for("login"))
        # Remember which user has logged in
        session["user_id"] = user_query["id"]

        # Redirect user to home page
        flash("You have successfully logged in!", "success")
        return redirect(url_for("index"))

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")

@app.route("/logout")
def logout():
=======
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
>>>>>>> 48a033c87744585695edfe9d4d5986930a0931fd

    # Forget any user_id
    session.clear()

    # Redirect user to login form
<<<<<<< HEAD
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():

    # Forget the user
    session.pop("user_id", None)
=======
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":

        symbol = request.form.get("symbol")

        row = lookup(symbol)
        if not row:
            return render_template("quote.html")
        return render_template("quoted.html", row = row)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    session.clear()

    def sh_apology(x):

        return apology("must provide " + x, 403)
>>>>>>> 48a033c87744585695edfe9d4d5986930a0931fd

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

<<<<<<< HEAD
        # Checking if the form is correct
        if not username:
            flash("You must provide a username!", "danger")
            return redirect(url_for("register"))

        elif not password:
            flash("You must provide a password!", "danger")
            return redirect(url_for("register"))

        elif not confirmation:
            flash("You must confirm your password!", "danger")
            return redirect(url_for("register"))

        elif confirmation != password:
            flash("Passwords don't match!", "danger")
            return redirect(url_for("register"))

        elif len(username) > 20:
            flash("Username can be maximum 20 characters long!", "danger")
            return redirect(url_for("register"))

        # Checking if the username exists
        user_query = db.execute(
            "SELECT * FROM users WHERE username = :username", 
            {"username": username}
        ).first()

        if user_query:
            flash("That username is already taken!", "warning")
            return redirect(url_for("register"))

        # Injecting the new user in the database
        db.execute(
            "INSERT INTO users (username, password) VALUES (:username, :hashpw)",
            {"username": username,
            "hashpw": generate_password_hash(password)}
        )

        db.commit()

        flash("You have successfully registered!", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html")
=======
        names = db.execute("SELECT username FROM users WHERE username = :username",
                          username=username)

        # Ensure username was submitted
        if not username:
            return sh_apology("username")

        elif names:
            return sh_apology("a genuine username")

        # Ensure password was submitted
        elif not password:
            return sh_apology("password")

        elif not confirmation:
            return sh_apology("confirmation")

        elif confirmation != password:
            return apology("passwords dont match", 403)

        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hashpw)", username = username, hashpw= generate_password_hash(password))

        return redirect("/")



    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    shares = db.execute("SELECT shares, SUM(num_of_shares) FROM purchases JOIN users ON purchases.user_id=users.id WHERE users.id = :session_id GROUP BY purchases.shares", session_id = session["user_id"])

    share_list = []

    for row in shares:
        list_row = {}

        share = lookup(row["shares"])["symbol"]
        owned_shares = row["SUM(num_of_shares)"]


        list_row["share"] = share
        list_row["owned_shares"] = owned_shares

        if owned_shares != 0:
            share_list.append(list_row)

    print(share_list)



    if request.method == "POST":

        symbol = request.form.get("symbol")

        share_n = request.form.get("shares", type=int)

        share_price = lookup(symbol)["price"]

        total_price = share_n * share_price

        users_credit = float(db.execute("SELECT cash FROM users WHERE id = :session_id", session_id = session["user_id"])[0]["cash"])


        if share_n < 0:
            return apology("Please provide valid number")

        for row in share_list:

            if row["share"] == symbol and share_n > row["owned_shares"]:

                return apology("You dont have enough shares")



        db.execute("UPDATE users SET cash= :cash WHERE id= :session_id", cash= users_credit + total_price, session_id = session["user_id"])

        db.execute("INSERT INTO purchases (user_id, shares, num_of_shares, at_price, time) VALUES(:session_id, :symbol, :share_n, :share_price, CURRENT_TIMESTAMP)", session_id = session["user_id"], symbol = symbol, share_n = -share_n, share_price = share_price)



    return render_template("sell.html", rows = share_list)







def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
>>>>>>> 48a033c87744585695edfe9d4d5986930a0931fd
