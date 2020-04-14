import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Initiate database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Create books table
db.execute("CREATE TABLE books(\
    id SERIAL PRIMARY KEY NOT NULL,\
    isbn VARCHAR,\
    title VARCHAR,\
    author VARCHAR,\
    year VARCHAR)")

# Open csv file
with open("books.csv", "r") as books:
    reader = csv.reader(books)

    # Skip the first row
    next(reader)

    # Insert each row data into the table
    for row in reader:
        book = {
            "isbn": row[0],
            "title": row[1],
            "author": row[2],
            "year": row[3]
        }
        db.execute("INSERT INTO books (isbn, title, author, year) \
            VALUES (:isbn, :title, :author, :year)", book)

    db.commit()