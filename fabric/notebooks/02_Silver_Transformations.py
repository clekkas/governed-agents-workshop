"""Starter Fabric notebook: transform bronze to silver tables."""

for dataset in ["patients", "encounters", "conditions", "medications", "vitals", "clinical_notes", "claims", "care_tasks"]:
    df = spark.table(f"bronze_{dataset}").dropDuplicates()
    df.write.mode("overwrite").format("delta").saveAsTable(f"silver_{dataset}")
    print(f"Wrote silver_{dataset}")

