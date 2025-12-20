# helpers/spark_session.py
from pyspark.sql import SparkSession # type: ignore[import]
import os

def build_spark(app_name: str) -> SparkSession:
    """
    SparkSession:
    - Delta Lake enabled (jars provided via spark-submit)
    - S3a / MinIO configured
    """

    s3_endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
    s3_access = os.getenv("S3_ACCESS_KEY", "minio")
    s3_secret = os.getenv("S3_SECRET_KEY", "minio123")

    spark = (
        SparkSession.builder
        .appName(app_name)

        # Delta Lake
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")

        # S3a / MinIO
        .config("spark.hadoop.fs.s3a.endpoint", s3_endpoint)
        .config("spark.hadoop.fs.s3a.access.key", s3_access)
        .config("spark.hadoop.fs.s3a.secret.key", s3_secret)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")

        .getOrCreate()
    )

    return spark


