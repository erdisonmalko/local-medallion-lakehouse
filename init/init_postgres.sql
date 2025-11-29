-- init_postgres.sql
CREATE TABLE IF NOT EXISTS customers (
  id SERIAL PRIMARY KEY,
  name TEXT,
  email TEXT,
  country TEXT,
  updated_at TIMESTAMP DEFAULT now()
);

INSERT INTO customers (name, email, country)
VALUES
('Alice','alice@example.com','US'),
('Bob','bob@example.com','UK'),
('Carla','carla@example.com','DE');
