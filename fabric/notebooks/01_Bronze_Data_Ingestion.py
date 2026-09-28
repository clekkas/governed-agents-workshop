"""Starter Fabric notebook: ingest synthetic CSVs into bronze tables."""

DATASETS = [
    "patients",
    "encounters",
    "conditions",
    "medications",
    "vitals",
    "clinical_notes",
    "claims",
    "care_tasks",
]

for dataset in DATASETS:
    source = f"Files/synthetic/{dataset}.csv"
    target = f"bronze_{dataset}"
    df = spark.read.option("header", True).csv(source)
    df.write.mode("overwrite").format("delta").saveAsTable(target)
    print(f"Wrote {target}")

