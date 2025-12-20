-- init_postgres.sql
CREATE TABLE IF NOT EXISTS customers (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  country TEXT NOT NULL,
  updated_at TIMESTAMP DEFAULT now()
);

INSERT INTO customers (name, email, country)
VALUES
('Alice','alice1@example.com','US'),
('Bob','bob@example.com','UK'),
('Carla','carla@example.com','DE');
