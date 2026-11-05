CREATE TABLE authors (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE
);

CREATE TABLE books (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_id integer NOT NULL REFERENCES authors(id),
    title text NOT NULL,
    price numeric(10, 2) NOT NULL CHECK (price > 0 AND price <> 'NaN')
);

CREATE TABLE customers (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    email text NOT NULL UNIQUE
);

CREATE TABLE orders (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id integer NOT NULL REFERENCES customers(id),
    status text NOT NULL CHECK (status IN ('new', 'paid', 'sent'))
);

CREATE TABLE order_items (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id integer NOT NULL REFERENCES orders(id),
    book_id integer NOT NULL REFERENCES books(id),
    quantity integer NOT NULL CHECK (quantity > 0),
    UNIQUE (order_id, book_id)
);
