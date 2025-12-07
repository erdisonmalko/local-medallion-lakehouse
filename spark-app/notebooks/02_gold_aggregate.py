# Gold aggregation: read silver and produce aggregates
# spark SQL functions
from pyspark.sql.functions import col, count # type: ignore

# local imports
from helpers.spark_session import build_spark

spark = build_spark('gold-aggregate')

silver_path = "s3a://silver/customers"
gold_path = "s3a://gold/customers_summary"

df = spark.read.format('delta').load(silver_path)

agg = df.groupBy('country').agg(count('*').alias('customers'))
agg.write.format('delta').mode('overwrite').save(gold_path)

print('Gold aggregate written, rows:', agg.count())
