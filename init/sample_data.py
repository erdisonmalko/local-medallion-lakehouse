# sample_data.py - insert more sample rows into Postgres to simulate incoming data
import psycopg2
from faker import Faker
fake = Faker()

conn = psycopg2.connect(host='127.0.0.1', dbname='sourcedb', user='admin', password='admin')
cur = conn.cursor()
for i in range(100):
    cur.execute("INSERT INTO customers (name, email, country) VALUES (%s,%s,%s)",
                (fake.name(), fake.email(), fake.country_code()))
conn.commit()
cur.close()
conn.close()
print('Inserted 100 sample rows')
