# Bronze ingest: chunked JDBC read -> write to Delta (s3a://bronze)
import time, random
from datetime import datetime

# local import
from helpers.spark_session import build_spark


spark = build_spark('bronze-ingest')

jdbc_url = "jdbc:postgresql://localhost:5432/sourcedb"
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
                print(f"Failed after {retries} retries: {e}")
                raise
            wait = base_delay * (2 ** (i-1)) + random.random()
            print(f"Retry {i}/{retries}, waiting {wait:.1f}s due to {e}")
            time.sleep(wait)

def get_last_offset():
    try:
        df = spark.read.format('delta').load(control_path)
        row = df.orderBy(df.last_offset.desc()).limit(1).collect()
        if row:
            offset = int(row[0]['last_offset'])
            print(f"Retrieved last offset from control: {offset}")
            return offset
    except Exception as e:
        print(f"Error reading control path (may be first run): {e}")
    print("No previous offset found, starting from 0")
    return 0

def read_chunk(offset, chunk_size=1000):
    query = f"(SELECT * FROM customers WHERE id > {offset} ORDER BY id LIMIT {chunk_size}) as t"
    print(f"Reading chunk from offset {offset} with size {chunk_size}")
    return spark.read.jdbc(jdbc_url, query, properties=jdbc_props)

offset = get_last_offset()
print(f'Starting from offset: {offset}')
print(f'Bronze path: {bronze_path}')
print(f'Control path: {control_path}')
print(f'Logs path: {logs_path}')

chunk_num = 0
while True:
    chunk_num += 1
    print(f'\n--- Chunk {chunk_num} ---')
    df = with_retries(lambda: read_chunk(offset, 1000))
    if df.rdd.isEmpty():
        print('No more rows to read. Ingestion complete.')
        break
    max_id = df.agg({'id':'max'}).collect()[0][0]
    rows = df.count()
    print(f"Read {rows} rows, max_id: {max_id}")
    
    with_retries(lambda: df.write.format('delta').mode('append').save(bronze_path))
    print(f"Written {rows} rows to {bronze_path}")
    
    # write control and logs
    spark.createDataFrame([(int(max_id),)] , ['last_offset']).write.format('delta').mode('append').save(control_path)
    print(f"Updated control with last_offset: {max_id}")
    
    spark.createDataFrame([(datetime.utcnow().isoformat(), int(offset), int(max_id), int(rows))],
                          ['ts','start_offset','end_offset','row_count']).write.format('delta').mode('append').save(logs_path)
    print(f"Logged ingest metadata to {logs_path}")
    
    offset = int(max_id)
    print(f'Completed chunk {chunk_num}: rows [{offset-rows+1}...{offset}]')

print('\nIngest job finished successfully')
