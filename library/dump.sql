CREATE DATABASE library;

CREATE TABLE genres (
    id serial PRIMARY KEY,
    genre VARCHAR(50) NOT NULL,
    CONSTRAINT genre_u UNIQUE(genre)
);

CREATE TABLE authors (
    id serial PRIMARY KEY,
    author_name varchar(50) NOT NULL,
    CONSTRAINT author_name_U UNIQUE(author_name)
);

CREATE TABLE books (
    id serial PRIMARY KEY,
    title varchar(50) NOT NULL,
    author_id integer NOT NULL DEFAULT 1,
    pages smallint DEFAULT(100) CHECK(pages >= 1),
    UNIQUE(title, author_id),
    CONSTRAINT fk_author FOREIGN KEY(author_id) REFERENCES authors(id) ON DELETE SET DEFAULT
);

CREATE TABLE book_genre (
    book_id integer NOT NULL,
    genre_id integer NOT NULL,
    UNIQUE(book_id, genre_id),
    CONSTRAINT fk_book
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE,
    CONSTRAINT fk_genre
        FOREIGN KEY(genre_id) REFERENCES genres(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS public.libraries
(
    id serial PRIMARY KEY,
    name varchar(50) NOT NULL,
    address varchar(50) NOT NULL,
    UNIQUE(name, address)
);

CREATE TABLE IF NOT EXISTS public.library_stock
(
    library_id integer NOT NULL,
    book_id integer NOT NULL,
    count integer NOT NULL DEFAULT 1 CHECK (count >= 0),
    UNIQUE(library_id, book_id),
    CONSTRAINT fk_library FOREIGN KEY (library_id)
        REFERENCES public.libraries (id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_book FOREIGN KEY (book_id)
        REFERENCES public.books (id)
        ON UPDATE NO ACTION
        ON DELETE CASCADE
);

INSERT INTO genres (genre) VALUES ('fiction'),('nonfiction'),('drama'),('poetry'),('folktale'),('history'),('fantasy'),('thriller'),('horror'),('romance'),('western'),('detective'),('mystery');
INSERT INTO authors (author_name) VALUES ('unknown'),('Stephen King'),('Dan Brown'),('J. K. Rowling'),('James Patterson'),('David Baldacci'),('Nora Roberts'),('Michael Connelly');
INSERT INTO books (title, author_id, pages) VALUES ('It', 2, 1231),('The Shining',2,447),('New Life',1,140),('Da Vinci Code',3,689),('Angels and Demons',3,768),('The Awakening: The Dragon Heart Legacy',7,419),('Harry Potter and the Philosopher''s Stone',4,223);
INSERT INTO book_genre VALUES (1,8),(1,9),(1,3),(2,1),(2,8),(2,9),(3,1),(4,12),(4,1),(4,8),(4,13),(5,13),(5,8),(6,10),(6,1),(6,7),(7,3),(7,7);
INSERT INTO libraries (name, address) VALUES ('New York Public Library', 'USA'),('Brooklyn Public Library', 'USA'), ('National Library of China','China'),('State Library of Victoria','Australia'),('British Library', 'UK');
INSERT INTO library_book VALUES (1,5,3),(1,1,1),(1,3,10),(2,6,2),(2,7,5);