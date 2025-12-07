# Silver transform: read bronze, run DQ checks, dedupe, merge into silver table
from helpers.spark_session import build_spark
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window

spark = build_spark('silver-transform')

bronze_path = "s3a://bronze/customers"
silver_path = "s3a://silver/customers"
bad_path = "s3a://silver/bad_records"
dq_path = "s3a://logs/dq_violations"

df = spark.read.format('delta').load(bronze_path)

# Simple DQ checks
null_email = df.filter(col('email').isNull())
if null_email.count() > 0:
    null_email.write.format('delta').mode('append').save(bad_path)
    spark.createDataFrame([('null_email', null_email.count())], ['check','count']).write.format('delta').mode('append').save(dq_path)

# Deduplicate by (id) keeping latest updated_at
w = Window.partitionBy('id').orderBy(col('updated_at').desc())
df_dedup = df.withColumn('rn', row_number().over(w)).filter(col('rn')==1).drop('rn')

# Merge into silver (simple overwrite here for demo)
df_dedup.write.format('delta').mode('overwrite').save(silver_path)
print('Silver transform completed, rows:', df_dedup.count())
