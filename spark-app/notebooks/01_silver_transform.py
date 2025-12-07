# Silver transform: read bronze, run DQ checks, dedupe, merge into silver table

# spark SQL functions
from pyspark.sql.functions import col, row_number # type: ignore
from pyspark.sql.window import Window # type: ignore

# local imports
from helpers.spark_session import build_spark


spark = build_spark('silver-transform')

bronze_path = "s3a://bronze/customers"
silver_path = "s3a://silver/customers"
bad_path = "s3a://silver/bad_records"
dq_path = "s3a://logs/dq_violations"

print(f"Reading from bronze path: {bronze_path}")
df = spark.read.format('delta').load(bronze_path)
print(f"Bronze records loaded: {df.count()}")

# Simple DQ checks
print("Starting DQ checks...")
null_email = df.filter(col('email').isNull())
null_count = null_email.count()
print(f"Null email records found: {null_count}")
if null_count > 0:
    null_email.write.format('delta').mode('append').save(bad_path)
    print(f"Bad records written to: {bad_path}")
    spark.createDataFrame([('null_email', null_count)], ['check','count']).write.format('delta').mode('append').save(dq_path)
    print(f"DQ violation logged to: {dq_path}")

# Deduplicate by (id) keeping latest updated_at
print("Deduplicating records by id...")
w = Window.partitionBy('id').orderBy(col('updated_at').desc())
df_dedup = df.withColumn('rn', row_number().over(w)).filter(col('rn')==1).drop('rn')
dedup_count = df_dedup.count()
print(f"Records after deduplication: {dedup_count}")

# Merge into silver (simple overwrite here for demo)
print(f"Writing silver data to: {silver_path}")
df_dedup.write.format('delta').mode('overwrite').save(silver_path)
print(f'Silver transform completed successfully. Total rows: {dedup_count}')
