# ./docker/spark/Dockerfile
FROM apache/spark:3.5.1

USER root

# Install Python 3.9 and pip
RUN apt-get update && \
    apt-get install -y python3.9 python3.9-venv python3-pip && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1 && \
    rm -rf /var/lib/apt/lists/*

# Install PySpark and Delta Lake Python package
RUN pip3 install --no-cache-dir pyspark delta-spark

# Set PySpark environment variables
ENV PYSPARK_PYTHON=/usr/bin/python3
ENV PYSPARK_DRIVER_PYTHON=/usr/bin/python3

USER spark