# Databricks notebook source
from pyspark.sql import functions as F

bronze_df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .option("quote", '"')
    .option("escape", '"')
    .csv("/Volumes/workspace/bronze/landing_zone/steam_bronze.csv")
)

bronze_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("workspace.bronze.steam_games")

print(f"Re-ingested {bronze_df.count()} rows")

bronze_df.filter(F.col("appid").isin(595280, 817820)) \
    .select("appid", "name", "release_date", "english", "owners", "price") \
    .show(truncate=False)

# COMMAND ----------

