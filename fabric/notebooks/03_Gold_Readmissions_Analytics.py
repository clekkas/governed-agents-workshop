"""Starter Fabric notebook: create readmissions analytics tables."""

from pyspark.sql.functions import col, count, count_if

encounters = spark.table("silver_encounters")

gold = (
    encounters.groupBy("facility", "primary_diagnosis")
    .agg(
        count("*").alias("encounter_count"),
        count_if(col("was_readmitted_30d") == "true").alias("readmission_count"),
    )
)

gold.write.mode("overwrite").format("delta").saveAsTable("gold_readmissions_summary")
print("Wrote gold_readmissions_summary")

