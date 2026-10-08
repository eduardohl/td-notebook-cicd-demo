# Databricks notebook source
# MAGIC %md
# MAGIC # Silly CI/CD Demo Notebook
# MAGIC
# MAGIC This same notebook is promoted `dev -> qa -> pat -> prod` by GitHub Actions.
# MAGIC The **code never changes** between environments. Only the bundle *target*
# MAGIC (workspace path + catalog/schema) changes, injected as job parameters.

# COMMAND ----------

dbutils.widgets.text("env", "dev")
dbutils.widgets.text("catalog", "dev_catalog")
dbutils.widgets.text("schema", "ingestion")

env = dbutils.widgets.get("env")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

print(f"Hello from the {env.upper()} environment!")
print(f"If this were real, I would write to {catalog}.{schema}")

# COMMAND ----------

from pyspark.sql import functions as F

df = (
    spark.range(5)
    .withColumn("env", F.lit(env))
    .withColumn("target_catalog", F.lit(catalog))
    .withColumn("target_schema", F.lit(schema))
)
df.show()

print(f"Demo rows produced in {env}. No real tables were harmed.")
