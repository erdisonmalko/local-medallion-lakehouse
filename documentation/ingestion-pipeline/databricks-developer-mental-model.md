# Databricks: Developer Mental Model

A practical guide to understanding Databricks architecture from a developer's perspective, not an architect's.

---

## Component Map

### **S3 = Your persistent storage layer**
- All your data lives here as Parquet files
- Databricks doesn't "store" data - it reads/writes to S3
- Think of S3 buckets as your raw disk: `s3://my-data-lake/bronze/`, `s3://my-data-lake/silver/`
- IAM policies control who can read/write these buckets
- **Your code never manages S3 directly** - you write to Delta tables, Delta manages the S3 paths

---

### **Delta Lake = SQL interface over S3**
- Makes S3 behave like a transactional database
- You run `INSERT`, `UPDATE`, `DELETE`, `MERGE` - Delta translates to S3 file operations
- The `_delta_log/` folder is the "transaction log" tracking what files are active
- **Time travel**: `SELECT * FROM table VERSION AS OF 10` reads old S3 snapshots
- **Developer view**: It's PostgreSQL, but the data happens to be in S3

---

### **Spark = The database engine**
- This is the compute layer that actually reads Parquet files and runs your SQL/Python
- Distributed query engine: splits work across executors (like parallel workers)
- **Lazy evaluation**: You build a query plan, Spark optimizes it, then executes when you call `.show()`, `.write()`, etc.
- Runs on clusters (EC2 instances) that Databricks manages for you
- **Developer view**: You're writing Spark code (`spark.sql()`, `df.write()`) - Spark figures out how to distribute the work

---

### **Unity Catalog = Governance + metadata layer**
- Central registry of "what tables exist and where"
- Maps `catalog.schema.table` → `s3://bucket/path/`
- **Permissions**: Who can read/write tables, schemas, catalogs
- **Lineage**: Tracks "this table was created from that notebook"
- **Storage Credentials + External Locations**: How Unity Catalog accesses S3 on your behalf
- **Developer view**: It's your `information_schema` + RBAC system. You grant permissions here, not in S3 bucket policies.

---

### **Workflows (Jobs) = Task scheduler (Airflow replacement)**
- Schedule notebooks, Python scripts, dbt runs, Delta Live Tables pipelines
- Define DAGs: Task A → Task B → Task C
- Parameterize runs: pass different `catalog` for dev/prod
- **Retries, alerts, cluster management** built-in
- **Developer view**: Like Airflow, but tightly integrated with Databricks. You define jobs via UI or API, not Python DAG files.

---

### **Databricks REST APIs = Programmatic access to everything**

The **Workspace API** lets you interact with every domain:

#### **Jobs API** (`/api/2.1/jobs`)
```bash
# Create a job
POST /api/2.1/jobs/create
{
  "name": "daily_etl",
  "tasks": [{
    "task_key": "ingest",
    "notebook_task": {"notebook_path": "/pipelines/ingest"}
  }],
  "schedule": {"quartz_cron_expression": "0 0 * * *"}
}

# Run a job
POST /api/2.1/jobs/run-now
{"job_id": 123}
```

#### **Secrets API** (`/api/2.0/secrets`)
```bash
# Create a secret scope
POST /api/2.0/secrets/scopes/create
{"scope": "prod-keys"}

# Store a secret
POST /api/2.0/secrets/put
{"scope": "prod-keys", "key": "openai-api-key", "string_value": "sk-..."}
```

#### **SQL API** (`/api/2.0/sql/statements`)
```bash
# Execute SQL and get results
POST /api/2.0/sql/statements
{
  "warehouse_id": "abc123",
  "statement": "SELECT COUNT(*) FROM prod.gold.customers"
}
```

#### **Unity Catalog API** (`/api/2.1/unity-catalog`)
```bash
# Create a catalog
POST /api/2.1/unity-catalog/catalogs
{"name": "dev", "comment": "Development environment"}

# Grant permissions
POST /api/2.1/unity-catalog/permissions/catalog/dev
{"principal": "data-engineers", "privilege": "USE_CATALOG"}
```

#### **Repos API** (`/api/2.0/repos`)
```bash
# Sync a Git repo
PATCH /api/2.0/repos/{repo_id}
{"branch": "main"}
```

**Developer view**: These APIs let you build CI/CD pipelines, automate job creation, manage secrets programmatically, run SQL from external services (like FastAPI hitting Databricks for analytics).

---

## How they connect (the flow)

```
1. You write code in a notebook or .py file
   ↓
2. Code runs on a Spark cluster (the engine)
   ↓
3. Spark reads/writes Delta tables (SQL interface)
   ↓
4. Delta translates to Parquet files in S3 (storage)
   ↓
5. Unity Catalog tracks metadata + enforces permissions (governance)
   ↓
6. Jobs API schedules this to run daily (orchestration)
   ↓
7. Secrets API provides credentials without hardcoding (security)
```

---

## Deep Dive: Developer Day-to-Day Details

### **1. You're writing against a SQL database... that happens to live in S3**

When you run:
```python
spark.sql("SELECT * FROM my_catalog.my_schema.customers")
```

What's actually happening:
- **Unity Catalog** is just a fancy metadata store - it knows "customers table = s3://bucket/path/to/customers/"
- **Delta Lake** gives you the magic: transaction log (`_delta_log/` folder) tracks what Parquet files are "in" the table
- Your code doesn't care about S3 paths - you reference tables, Unity Catalog resolves them

**Developer takeaway**: You almost never write `spark.read.parquet("s3://...")` directly anymore. You use catalog.schema.table and let Unity Catalog handle the plumbing.

---

### **2. IAM/permissions - two separate worlds**

**Cluster-level IAM role** (the EC2 instance):
- This is what your Spark driver/executors run as
- Needs S3 read/write to wherever your data lives
- Needs read on the Unity Catalog metastore (usually in a separate AWS account)

**Storage Credentials + External Locations** (Unity Catalog layer):
- This is how Unity Catalog *itself* accesses S3 on your behalf
- You create a **Storage Credential** (basically an IAM role ARN that Unity Catalog can assume)
- Then create an **External Location** pointing to `s3://my-bucket/path/` with that credential
- Tables/volumes inherit permissions from these

**The confusing part**: When you write data, *both* need permission:
1. Your cluster IAM role writes the Parquet files
2. Unity Catalog's storage credential needs to read them to register metadata

---

### **3. Delta Lake - it's just files + a transaction log**

```
s3://bucket/data/customers/
├── _delta_log/
│   ├── 00000000000000000000.json  # "add file1.parquet, remove file2.parquet"
│   ├── 00000000000000000001.json
│   └── 00000000000000000010.checkpoint.parquet  # periodic snapshot
├── part-00000-xxx.snappy.parquet
├── part-00001-xxx.snappy.parquet
└── part-00002-xxx.snappy.parquet  # might be logically deleted but still exists
```

When you `DELETE FROM customers WHERE id = 5`:
- Delta writes a new JSON entry: "remove part-00001.parquet, add part-00003.parquet"
- The old file stays in S3 (for time travel)
- Reads consult `_delta_log/` to know which files are "active"

**Developer takeaway**: 
- `VACUUM` is what actually deletes old files (default: keeps 7 days for time travel)
- `OPTIMIZE` compacts small files into bigger ones (important for query perf)
- You can `.option("versionAsOf", 3)` to read old versions

---

### **4. Writing data - three common patterns**

**Append** (logs, events):
```python
df.write.mode("append").saveAsTable("catalog.schema.events")
```

**Overwrite** (full refresh):
```python
df.write.mode("overwrite").saveAsTable("catalog.schema.dim_customers")
```

**Merge/Upsert** (SCD Type 1):
```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forName(spark, "catalog.schema.customers")
delta_table.alias("target").merge(
    updates_df.alias("source"),
    "target.id = source.id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

**The gotcha**: If your cluster IAM role doesn't have S3 write access, you get cryptic errors like "Access Denied" deep in the stack trace.

---

### **5. The Unity Catalog namespace hierarchy**

```
metastore  (one per region, shared across workspaces)
└── catalog  (like a "database" in traditional DBs)
    └── schema  (like a "schema" in Postgres)
        └── table/view/volume
```

**Three-part naming**: `catalog.schema.table`

**Why it matters**:
- You can have `dev.bronze.customers` and `prod.bronze.customers` in the same workspace
- Permissions are hierarchical: grant `USE CATALOG dev` to your service principal, it can read all schemas underneath
- **Volumes** are new - they're like tables but for non-tabular files (PDFs, images). Still live in S3, still tracked by Unity Catalog.

---

### **6. Secrets - don't hardcode them**

```python
# BAD
api_key = "sk-abc123..."

# GOOD (Databricks Secrets)
api_key = dbutils.secrets.get(scope="my-scope", key="openai-api-key")
```

You create scopes via CLI or UI, back them with Azure Key Vault or AWS Secrets Manager. Your notebooks reference them but never see the plaintext.

---

### **7. Streaming - it's just structured streaming with Delta as the sink**

```python
(spark.readStream
  .format("cloudFiles")  # Auto Loader - ingests S3 files incrementally
  .option("cloudFiles.format", "json")
  .load("s3://landing-bucket/events/")
  .writeStream
  .format("delta")
  .option("checkpointLocation", "s3://checkpoints/events")
  .toTable("catalog.bronze.events"))
```

**Developer POV**:
- Checkpoints track which files you've processed (so restarts don't duplicate)
- Delta as the sink gives you exactly-once semantics
- `cloudFiles` is Databricks' magic for incremental file ingestion (better than watching S3 yourself)

---

### **8. Debugging S3 access issues**

When you get `Access Denied`:

1. **Check cluster IAM role** (Compute → your cluster → AWS attributes):
   ```bash
   # In notebook
   spark.read.text("s3://your-bucket/test.txt").show()
   ```
   If this fails, your cluster IAM role is wrong.

2. **Check Unity Catalog external location**:
   ```sql
   SHOW EXTERNAL LOCATIONS;
   -- Does the path you're writing to match one of these?
   ```

3. **Check grants**:
   ```sql
   SHOW GRANTS ON EXTERNAL LOCATION `my-location`;
   ```

**Common mistake**: Your cluster can read S3, but Unity Catalog's storage credential can't → table creation fails with weird errors.

---

## Quick mental checklist when you start a new project

- [ ] **Catalog/schema created?** (`CREATE CATALOG dev; CREATE SCHEMA dev.bronze;`)
- [ ] **External location set up?** (for wherever your raw data lands)
- [ ] **Cluster has IAM role** with S3 access
- [ ] **Service principal** created if running jobs (not your personal account)
- [ ] **Secrets** configured for any API keys

---

## Practical Developer Scenarios

### **Scenario 1: Daily ETL pipeline**
- **Workflow (Job)** triggers at 2am
- **Spark** reads raw JSON from `s3://landing/events/`
- Writes to **Delta table** `dev.bronze.events` (which maps to `s3://lake/bronze/events/`)
- **Unity Catalog** enforces: only `data-engineers` group can write to `bronze`
- **Secrets API** provides AWS credentials to read from the landing bucket

### **Scenario 2: Ad-hoc analysis**
- You run `spark.sql("SELECT * FROM prod.gold.revenue")` in a notebook
- **Unity Catalog** checks: do you have `SELECT` on `prod.gold.revenue`?
- **Spark** plans the query, reads Parquet files from `s3://lake/gold/revenue/`
- **Delta** consults `_delta_log/` to know which files are current

### **Scenario 3: External app queries Databricks**
- Your **FastAPI backend** needs to fetch aggregated stats
- Calls **SQL API**: `POST /api/2.0/sql/statements` with a query
- Databricks executes on a **SQL Warehouse** (serverless Spark)
- Returns JSON results to your API
- **Unity Catalog** enforces: this service principal can only read `prod.gold.*`

---

## The "Aha" Moments

1. **Databricks doesn't own your data** - it's all in S3. Databricks is the compute + governance layer on top.
2. **Unity Catalog is not a database** - it's a metadata registry. The actual data is Delta/Parquet in S3.
3. **Jobs are not limited to notebooks** - you can schedule Python wheels, JARs, dbt, anything.
4. **APIs let you treat Databricks like a backend service** - you're not stuck in the UI. You can integrate it into your existing CI/CD, monitoring, or applications.
5. **IAM has two layers** - cluster-level (EC2) and Unity Catalog storage credentials. Both need correct permissions for writes to work.
6. **Delta Lake is just Parquet + transaction log** - the magic is in `_delta_log/`, not some proprietary format.

---

## Resources for Going Deeper

- **Unity Catalog docs**: Understanding storage credentials and external locations
- **Delta Lake transaction log spec**: How `_delta_log/` actually works
- **Databricks REST API reference**: Complete API documentation for all endpoints
- **Auto Loader (cloudFiles) guide**: Best practices for incremental ingestion
- **Structured Streaming + Delta**: Exactly-once semantics and checkpoint management

---

**Last updated**: May 2026  
**Perspective**: Backend developer / Data engineer, not architect
