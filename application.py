import os

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
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget the user
    session.pop("user_id", None)

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
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

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():

    # Forget the user
    session.pop("user_id", None)

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

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