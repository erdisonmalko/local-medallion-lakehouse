import sys

import psycopg2
from faker import Faker

fake = Faker()

def connect_db():
    try:
        # use .env file for production code
        conn = psycopg2.connect(
            host='127.0.0.1',
            dbname='sourcedb',
            user='admin',
            password='admin'
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def ensure_table(cur):
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100) UNIQUE,
                country VARCHAR(10)
            )
        """)
    except Exception as e:
        print(f"Error ensuring table exists: {e}")
        sys.exit(1)

def insert_sample_rows(cur, count=1000):
    inserted = 0
    for i in range(count):
        try:
            cur.execute(
                "INSERT INTO customers (name, email, country) VALUES (%s,%s,%s) ON CONFLICT (email) DO NOTHING",
                (fake.name(), fake.email(), fake.country_code())
            )
            inserted += cur.rowcount
        except psycopg2.errors.UniqueViolation:
            print(f"Duplicate email, skipping row {i}")
            continue
        except Exception as e:
            print(f"Error inserting row {i}: {e}")
            continue
    return inserted

def main():
    conn = connect_db()
    cur = conn.cursor()
    ensure_table(cur)
    rows_to_insert = 1000
    print(f"Inserting {rows_to_insert} sample rows...")
    inserted = insert_sample_rows(cur, rows_to_insert)
    conn.commit()
    cur.close()
    conn.close()
    print(f'Inserted {inserted} new sample rows (out of {rows_to_insert} attempts)')

if __name__ == "__main__":
    main()
