from typing import Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import psycopg2
import config

app = FastAPI()

class Book(BaseModel):
    id: Optional[int]
    title: str
    author: str
    genres: Optional[list]
    pages: Optional[int]


class Library(BaseModel):
    name: str
    address: str


class Stock(BaseModel):
    lib_name: str
    lib_address: str
    book_title: str
    book_author: str
    count: int


try:
    connection = psycopg2.connect(
        host=config.host,
        user=config.user,
        password=config.password,
        database=config.db_name
    )
    connection.autocommit = True
    cursor = connection.cursor()
except Exception as e:
    print("[ERROR]", e)


@app.get("/books")
def get_books(sort_by: str = "id", sort_order: str = "asc", min_pages: int = 1, max_pages: int = 10000, title: Optional[str] = None, author: Optional[str] = None, genre: Optional[str] = None):
    try:
        query = f"""SELECT DISTINCT b.id id, b.title title, a.author_name author, b.pages pages, g.genre from books b
                    JOIN authors a ON a.id = b.author_id
                    JOIN book_genre bg ON bg.book_id = b.id
                    JOIN genres g ON g.id = bg.genre_id 
                    WHERE pages >= {min_pages} AND pages <= {max_pages}"""
        if title:
            query += f" AND b.title = '{title}'"
        if author:
            query += f" AND a.author_name = '{author}'"
        if genre:
            query += f""" AND b.id IN (
                        SELECT b.id FROM books b
                        JOIN book_genre bg ON bg.book_id = b.id
                        JOIN genres g ON g.id = bg.genre_id
                        WHERE g.genre = '{genre}'
                    )"""
        query += f" ORDER BY {sort_by} {sort_order}"
        cursor.execute(query)
        data = cursor.fetchall()
        books = {}
        for row in data:
            id = row[0]
            if id in books:
                books[id].genres.append(row[4])
            else:
                books[id] = Book(
                    id = id,
                    title = row[1],
                    author = row[2],
                    pages = row[3],
                    genres = [row[4]]
                )
        return {"books": books}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@app.get("/book")
def get_book(title: str = None, author: str = None):
    # fetching exactly 1 book
    if title and author:
        try:
            cursor.execute("""SELECT DISTINCT b.id, b.title, a.author_name, b.pages, g.genre from books b
                        JOIN authors a ON a.id = b.author_id
                        JOIN book_genre bg ON bg.book_id = b.id
                        JOIN genres g ON g.id = bg.genre_id
                        WHERE b.title = %s AND a.author_name = %s""",
                        (title, author))
            data = cursor.fetchall()
            book = Book(
                id = data[0][0],
                title = data[0][1],
                author = data[0][2],
                pages = data[0][3],
                genres = []
            )
            for row in data:
                book.genres.append(row[4])
            return {
                book.id: {
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genres,
                    "pages": book.pages
                }
            }
        except Exception as e:
            print("[ERROR]", e)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@app.post("/book")
def add_book(book: Book):
    # check if book is already in DB
    cursor.execute("SELECT 1 FROM books WHERE title = %s AND author_id = (SELECT id FROM authors WHERE author_name = %s)", (book.title, book.author))
    # not in DB
    if not cursor.fetchone():
        # unknown author - id 1
        if not book.author.strip():
            author_id = 1
        else:
            cursor.execute("SELECT id FROM authors WHERE author_name = %s", (book.author,))
            try:
                author_id = cursor.fetchone()[0]
            except:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown author")
        try:
            cursor.execute("INSERT INTO books (title, author_id, pages) VALUES (%s, %s, %s)", (book.title, author_id, book.pages))
        except Exception as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        cursor.execute("SELECT max(id) FROM books")
        book.id = cursor.fetchone()[0]
        for genre in book.genres:
            try:
                cursor.execute("INSERT INTO book_genre (book_id, genre_id) VALUES (%s, (SELECT id FROM genres WHERE genre = %s))", (book.id, genre))
            except Exception as e:
                print("[ERROR]", e)
        raise HTTPException(status_code=status.HTTP_201_CREATED)
    # book is already in DB
    else:
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="This book exists")


@app.delete("/book")
def delete_book(book: Book):
    # deleting book
    cursor.execute("SELECT 1 FROM books WHERE title = %s AND author_id = (SELECT id FROM authors WHERE author_name = %s)", (book.title, book.author))
    if cursor.fetchone():
        cursor.execute("DELETE FROM books WHERE title = %s AND author_id = (SELECT id FROM authors WHERE author_name = %s)", (book.title, book.author))
        raise HTTPException(status_code=status.HTTP_200_OK)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@app.get("/authors")
def get_authors():
    cursor.execute("SELECT * FROM authors")
    authors = {}
    for row in cursor.fetchall():
        authors[row[0]] = row[1]
    return authors


@app.post("/author")
def add_author(author_name: str):
    # check if author is already in DB
    cursor.execute("SELECT 1 FROM authors WHERE author_name = %s", (author_name,))
    # no
    if not cursor.fetchone():
        cursor.execute("INSERT INTO authors (author_name) VALUES (%s)", (author_name,))
        raise HTTPException(status_code=status.HTTP_200_OK, detail="added author")
    # yes
    else:
        raise HTTPException(status_code=status.HTTP_306_RESERVED, detail="author is already in DB")


@app.delete("/author")
def delete_author(author_name: str):
    # delete author if exists
    cursor.execute("SELECT 1 FROM authors WHERE author_name = %s", (author_name,))

    if cursor.fetchone():
        cursor.execute("DELETE FROM authors WHERE author_name = %s", (author_name,))
        raise HTTPException(status_code=status.HTTP_200_OK)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@app.get("/libs")
def get_libs():
    # fetching libraries
    cursor.execute("SELECT id, name, address FROM libraries")
    libs = {}
    for row in cursor.fetchall():
        libs[row[0]] = {
            "name": row[1],
            "address": row[2]
        }
    return libs


@app.post("/lib")
def add_lib(lib: Library):
    # adding new library
    try:    
        cursor.execute("INSERT INTO libraries (name, address) VALUES (%s, %s)", (lib.name, lib.address))
        return {
            "detail": f"Added library ({lib.name}, {lib.address})"
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Library ({lib.name}, {lib.address}) was not added")


@app.delete("/lib")
def delete_lib(lib: Library):
    # delete library if exists
    cursor.execute("SELECT 1 FROM libraries WHERE name = %s AND address = %s", (lib.name, lib.address))
    if cursor.fetchone():
        cursor.execute("DELETE FROM libraries WHERE name = %s", (lib.name,))
        raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Library ({lib.name}) deleted")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Library ({lib.name}) was not found")


@app.post("/lib/stock")
def update_lib_stock(stock: Stock):
    # Put book in library's stock
    try:
        cursor.execute("SELECT id FROM libraries WHERE name = %s AND address = %s", (stock.lib_name, stock.lib_address))
        lib_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM books WHERE title = %s AND author_id = (SELECT id FROM authors WHERE author_name = %s)", (stock.book_title, stock.book_author))
        book_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO library_stock (library_id, book_id, count) VALUES (%s, %s, %s)", (lib_id, book_id, stock.count))
        return "library stock updated"
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@app.get("/search")
def search(q: str = None):
    # search through related public data to hint
    if q:
        cursor.execute(f"""SELECT * FROM (
                            SELECT 'book', title search FROM books
                            union
                            SELECT 'author', author_name FROM authors
                            union
                            SELECT 'library', name FROM libraries
                            ) as foo
                        WHERE LOWER(search) LIKE '%{q.lower()}%'""")
        hints = {}
        for row in cursor.fetchall():
            hints[row[1]] = row[0]
        return {"hints": hints}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)