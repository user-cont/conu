CREATE TABLE products (id INTEGER, name VARCHAR(256), price FLOAT, variant INTEGER);
CREATE TABLE products_variant (id INTEGER, name VARCHAR(256));
INSERT INTO products_variant (id, name) VALUES ('1', 'blue'), ('2', 'green');

