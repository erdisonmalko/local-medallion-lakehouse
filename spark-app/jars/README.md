# jars/

## Purpose

This directory stores JAR files required for database connectivity in Spark applications. These dependencies enable the Spark driver and workers to establish connections to various data sources.

## Contents

- PostgreSQL JDBC driver
- SQL Server JDBC driver
- Additional database connectors as needed

## Usage

JAR files in this directory are automatically loaded by the Spark worker nodes during job execution, allowing seamless connections to configured database systems.

## Adding Dependencies

Place required JDBC drivers and connector libraries in this directory before running Spark jobs.
