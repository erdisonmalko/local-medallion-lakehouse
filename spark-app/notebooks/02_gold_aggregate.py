# Gold aggregation: read silver and produce aggregates
# spark SQL functions
from pyspark.sql.functions import col, count # type: ignore

# local imports
from helpers.spark_session import build_spark

spark = build_spark('gold-aggregate')

silver_path = "s3a://silver/customers"
gold_path = "s3a://gold/customers_summary"

print(f'Reading data from silver path: {silver_path}')
df = spark.read.format('delta').load(silver_path)
print(f'Data read successfully, number of rows: {df.count()}')

print('Aggregating data by country...')
agg = df.groupBy('country').agg(count('*').alias('customers'))
print('Aggregation complete, number of rows in aggregated data:', agg.count())

print(f'Writing aggregated data to gold path: {gold_path}')
agg.write.format('delta').mode('overwrite').save(gold_path)

print('Gold aggregate written, rows:', agg.count())
