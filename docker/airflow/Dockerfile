# ./docker/airflow/Dockerfile
# 1. Use the tag specifically for Python 3.9
FROM apache/airflow:2.10.4-python3.9

USER root

# 2. Add 'bullseye' (debian 11) repo to get openjdk-11, then install
RUN echo "deb http://deb.debian.org/debian bullseye main" > /etc/apt/sources.list.d/bullseye.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends openjdk-11-jdk wget unzip && \
    # Clean up the bullseye list to avoid future package conflicts
    rm /etc/apt/sources.list.d/bullseye.list && \
    rm -rf /var/lib/apt/lists/*

# 3. Download Spark 3.5.1 with Hadoop 3
RUN wget https://archive.apache.org/dist/spark/spark-3.5.1/spark-3.5.1-bin-hadoop3.tgz -O /tmp/spark.tgz && \
    tar xzf /tmp/spark.tgz -C /opt && \
    mv /opt/spark-3.5.1-bin-hadoop3 /opt/spark && \
    rm /tmp/spark.tgz

# 4. Set Spark environment variables
ENV SPARK_HOME=/opt/spark
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$SPARK_HOME/bin:$JAVA_HOME/bin:$PATH

USER airflow



