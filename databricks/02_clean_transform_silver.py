# Databricks notebook source
from pyspark.sql import functions as F

bronze_df = spark.table("workspace.bronze.steam_games")

# --- 1. Cleaned single-row-per-game table ---
# Use regexp_extract to ONLY extract digits - this CANNOT fail
owners_pattern = r"^\s*(\d+)\s*-\s*(\d+)\s*$"

games_silver = (
    bronze_df
    .withColumn("name", F.trim(F.col("name")))
    .withColumn("release_date", F.expr("try_to_date(release_date, 'yyyy-MM-dd')"))
    .withColumn("release_year", F.year(F.col("release_date")))
    .withColumn("english", F.col("english").try_cast("boolean"))
    .withColumn("developer", F.coalesce(F.col("developer"), F.lit("Unknown")))
    .withColumn("publisher", F.coalesce(F.col("publisher"), F.lit("Unknown")))
    
    # FIX: Safely handle price column (might have string values due to CSV shift)
    .withColumn("price_safe", F.col("price").try_cast("double"))
    .withColumn("is_free", F.col("price_safe") == 0)
    
    # FIX: Use regexp_extract to get ONLY digits - guaranteed safe cast
    .withColumn("owners_min_str", F.regexp_extract(F.col("owners"), owners_pattern, 1))
    .withColumn("owners_max_str", F.regexp_extract(F.col("owners"), owners_pattern, 2))
    .withColumn("owners_min", F.when(F.col("owners_min_str") != "", F.col("owners_min_str").cast("long")).otherwise(F.lit(None)))
    .withColumn("owners_max", F.when(F.col("owners_max_str") != "", F.col("owners_max_str").cast("long")).otherwise(F.lit(None)))
    .withColumn("owners_avg", ((F.col("owners_min") + F.col("owners_max")) / 2).cast("long"))
    
    .select(
        "appid", "name", "release_date", "release_year", "english",
        "developer", "publisher", "required_age",
        "categories", "steamspy_tags",
        "achievements", "positive_ratings", "negative_ratings",
        "average_playtime", "median_playtime",
        "owners_min", "owners_max", "owners_avg",
        F.col("price_safe").alias("price"), "is_free"
    )
)

games_silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("workspace.silver.games")

# --- 2. Genre bridge table ---
game_genres_silver = (
    bronze_df
    .select("appid", F.explode(F.split(F.col("genres"), ";")).alias("genre"))
    .withColumn("genre", F.trim(F.col("genre")))
    .filter(F.col("genre") != "")
)
game_genres_silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("workspace.silver.game_genres")

# --- 3. Platform bridge table ---
game_platforms_silver = (
    bronze_df
    .select("appid", F.explode(F.split(F.col("platforms"), ";")).alias("platform"))
    .withColumn("platform", F.trim(F.col("platform")))
    .filter(F.col("platform") != "")
)
game_platforms_silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("workspace.silver.game_platforms")

# Print counts to verify
print("games_silver:", games_silver.count())
print("null owners_min count:", games_silver.filter(F.col("owners_min").isNull()).count())
print("game_genres_silver:", game_genres_silver.count())
print("game_platforms_silver:", game_platforms_silver.count())

# COMMAND ----------

