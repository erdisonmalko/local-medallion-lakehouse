from pyspark.sql import SparkSession # type: ignore

def build_spark(app_name='local-dbx'):
    builder = SparkSession.builder.appName(app_name).master("local[*]")
    # Delta core package
    builder = builder.config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0")
    # MinIO / s3a settings (override when running in containers)
    builder = builder.config("spark.hadoop.fs.s3a.endpoint", "http://127.0.0.1:9001")
    builder = builder.config("spark.hadoop.fs.s3a.access.key", "minio")
    builder = builder.config("spark.hadoop.fs.s3a.secret.key", "minio123")
    builder = builder.config("spark.hadoop.fs.s3a.path.style.access", "true")
    builder = builder.config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    builder = builder.config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    return builder.getOrCreate()
