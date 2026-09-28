# DAX Measures

```DAX
Readmission Rate =
DIVIDE(
    SUM('gold_readmissions_summary'[readmission_count]),
    SUM('gold_readmissions_summary'[encounter_count])
)
```

```DAX
Total Encounters =
SUM('gold_readmissions_summary'[encounter_count])
```

