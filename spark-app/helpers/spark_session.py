# helpers/spark_session.py
from pyspark.sql import SparkSession # type: ignore[import]
import os

def build_spark(app_name: str) -> SparkSession:
    """
    Build a SparkSession configured for:
    - Delta Lake (fetched online via Maven)
    - S3a (MinIO) access
    - PostgreSQL JDBC (requires local jar)
    """

    # S3 / MinIO config
    s3_endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
    s3_access = os.getenv("S3_ACCESS_KEY", "minio")
    s3_secret = os.getenv("S3_SECRET_KEY", "minio123")

    # Path to local JDBC jar(inside the container)
    postgres_jar = "/opt/spark-app/jars/postgresql-42.6.0.jar"

    spark = (
        SparkSession.builder
        .appName(app_name)
        # Delta Lake extensions
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        # S3 / MinIO
        .config("spark.hadoop.fs.s3a.endpoint", s3_endpoint)
        .config("spark.hadoop.fs.s3a.access.key", s3_access)
        .config("spark.hadoop.fs.s3a.secret.key", s3_secret)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        # Jars
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,io.delta:delta-core_2.12:2.4.0")  # online
        .config("spark.jars", postgres_jar)  # local JDBC
        .getOrCreate()
    )

    return spark

