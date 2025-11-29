# Gold aggregation: read silver and produce aggregates
from helpers.spark_session import build_spark
from pyspark.sql.functions import col, count
spark = build_spark('gold-aggregate')

silver_path = "s3a://silver/customers"
gold_path = "s3a://gold/customers_summary"

df = spark.read.format('delta').load(silver_path)

agg = df.groupBy('country').agg(count('*').alias('customers'))
agg.write.format('delta').mode('overwrite').save(gold_path)

print('Gold aggregate written, rows:', agg.count())
