INSERT INTO authors (name) VALUES ('Александр Пушкин'), ('Николай Гоголь'), ('Антон Чехов');
INSERT INTO books (author_id, title, price) VALUES
    (1, 'Капитанская дочка', 390.00),
    (2, 'Мёртвые души', 490.00),
    (3, 'Вишнёвый сад', 320.00),
    (1, 'Евгений Онегин', 450.00);
INSERT INTO customers (name, email) VALUES
    ('Анна', 'anna@example.test'), ('Иван', 'ivan@example.test');
INSERT INTO orders (customer_id, status) VALUES (1, 'paid'), (2, 'new');
INSERT INTO order_items (order_id, book_id, quantity) VALUES (1, 1, 1), (1, 2, 2), (2, 3, 1);
