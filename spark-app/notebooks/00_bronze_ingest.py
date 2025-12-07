# Bronze ingest: chunked JDBC read -> write to Delta (s3a://bronze)
import time, random
from datetime import datetime

# local import
from helpers.spark_session import build_spark


spark = build_spark('bronze-ingest')

jdbc_url = "jdbc:postgresql://127.0.0.1:5432/sourcedb"
jdbc_props = {"user":"admin","password":"admin","driver":"org.postgresql.Driver"}

bronze_path = "s3a://bronze/customers"
control_path = "s3a://control/ingest_control"
logs_path = "s3a://logs/ingest_logs"

def with_retries(fn, retries=5, base_delay=2.0):
    for i in range(1, retries+1):
        try:
            return fn()
        except Exception as e:
            if i == retries:
                raise
            wait = base_delay * (2 ** (i-1)) + random.random()
            print(f"Retry {i}/{retries}, waiting {wait:.1f}s due to {e}")
            time.sleep(wait)

def get_last_offset():
    try:
        df = spark.read.format('delta').load(control_path)
        row = df.orderBy(df.last_offset.desc()).limit(1).collect()
        if row:
            return int(row[0]['last_offset'])
    except Exception:
        pass
    return 0

def read_chunk(offset, chunk_size=1000):
    query = f"(SELECT * FROM customers WHERE id > {offset} ORDER BY id LIMIT {chunk_size}) as t"
    return spark.read.jdbc(jdbc_url, query, properties=jdbc_props)

offset = get_last_offset()
print('Starting from offset', offset)

while True:
    df = with_retries(lambda: read_chunk(offset, 1000))
    if df.rdd.isEmpty():
        print('No more rows to read.')
        break
    max_id = df.agg({'id':'max'}).collect()[0][0]
    rows = df.count()
    with_retries(lambda: df.write.format('delta').mode('append').save(bronze_path))
    # write control and logs
    spark.createDataFrame([(int(max_id),)] , ['last_offset']).write.format('delta').mode('append').save(control_path)
    spark.createDataFrame([(datetime.utcnow().isoformat(), int(offset), int(max_id), int(rows))],
                          ['ts','start_offset','end_offset','row_count'])         .write.format('delta').mode('append').save(logs_path)
    offset = int(max_id)
    print(f'Wrote rows up to id {offset}')
