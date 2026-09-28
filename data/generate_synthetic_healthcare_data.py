"""Generate small synthetic healthcare datasets for the workshop.

All records are fictional and intended for architecture and engineering labs only.
"""

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path


random.seed(42)

FACILITIES = ["Metro General", "Community Medical", "Riverside Health"]
DIAGNOSES = ["CHF", "COPD", "Pneumonia", "Diabetes", "Hypertension"]
DISPOSITIONS = ["Home", "Home Health", "Skilled Nursing Facility", "Rehab"]
PAYERS = ["Medicare", "Medicaid", "Commercial", "Self-Pay"]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/synthetic")
    parser.add_argument("--patients", type=int, default=60)
    args = parser.parse_args()

    output = Path(args.output)
    start = date(2026, 1, 1)

    patients = []
    encounters = []
    conditions = []
    medications = []
    vitals = []
    notes = []
    claims = []
    care_tasks = []

    for i in range(1, args.patients + 1):
        patient_id = f"P{i:04d}"
        age = random.randint(45, 88)
        facility = random.choice(FACILITIES)
        diagnosis = random.choice(DIAGNOSES)
        risk_score = round(random.uniform(0.1, 0.95), 2)
        risk_tier = "High" if risk_score >= 0.7 else "Medium" if risk_score >= 0.4 else "Low"

        patients.append(
            {
                "patient_id": patient_id,
                "age": age,
                "gender": random.choice(["F", "M"]),
                "primary_facility": facility,
                "risk_score": risk_score,
                "risk_tier": risk_tier,
            }
        )

        encounter_count = random.randint(1, 4)
        for j in range(1, encounter_count + 1):
            encounter_id = f"E{i:04d}-{j}"
            admit = start + timedelta(days=random.randint(0, 220))
            los = random.randint(1, 9)
            discharge = admit + timedelta(days=los)
            readmitted = j == 1 and random.random() < 0.18
            disposition = random.choice(DISPOSITIONS)

            encounters.append(
                {
                    "encounter_id": encounter_id,
                    "patient_id": patient_id,
                    "facility": facility,
                    "encounter_type": random.choice(["Inpatient", "ED", "Outpatient"]),
                    "admit_date": admit.isoformat(),
                    "discharge_date": discharge.isoformat(),
                    "length_of_stay_days": los,
                    "primary_diagnosis": diagnosis,
                    "discharge_disposition": disposition,
                    "was_readmitted_30d": str(readmitted).lower(),
                }
            )

            conditions.append(
                {
                    "condition_id": f"C{i:04d}-{j}",
                    "patient_id": patient_id,
                    "encounter_id": encounter_id,
                    "code": random.choice(["I50.9", "J44.1", "J18.9", "E11.9", "I10"]),
                    "description": diagnosis,
                    "status": random.choice(["active", "historical"]),
                }
            )

            medications.append(
                {
                    "medication_id": f"M{i:04d}-{j}",
                    "patient_id": patient_id,
                    "encounter_id": encounter_id,
                    "medication_name": random.choice(["Furosemide", "Metformin", "Albuterol", "Lisinopril"]),
                    "frequency": random.choice(["daily", "twice daily", "as needed"]),
                }
            )

            vitals.append(
                {
                    "vital_id": f"V{i:04d}-{j}",
                    "patient_id": patient_id,
                    "encounter_id": encounter_id,
                    "heart_rate": random.randint(62, 118),
                    "systolic_bp": random.randint(92, 168),
                    "temperature_f": round(random.uniform(97.0, 101.8), 1),
                    "spo2_percent": random.randint(88, 99),
                }
            )

            notes.append(
                {
                    "note_id": f"N{i:04d}-{j}",
                    "patient_id": patient_id,
                    "encounter_id": encounter_id,
                    "note_type": "Discharge Planning Note",
                    "note_text": (
                        f"Synthetic discharge-planning note for {diagnosis}. "
                        f"Follow-up planning was initiated for human review. "
                        f"Medication reconciliation and care coordination tasks were documented."
                    ),
                }
            )

            charge = random.randint(4500, 42000)
            denied = random.random() < 0.14
            claims.append(
                {
                    "claim_id": f"CL{i:04d}-{j}",
                    "patient_id": patient_id,
                    "encounter_id": encounter_id,
                    "payer": random.choice(PAYERS),
                    "claim_amount": charge,
                    "paid_amount": 0 if denied else int(charge * random.uniform(0.55, 0.9)),
                    "claim_status": "Denied" if denied else "Paid",
                }
            )

        if risk_tier in {"High", "Medium"}:
            care_tasks.append(
                {
                    "task_id": f"T{i:04d}",
                    "patient_id": patient_id,
                    "risk_tier": risk_tier,
                    "status": "PendingReview",
                    "assigned_role": "Care Manager",
                    "due_date": (start + timedelta(days=250 + random.randint(1, 14))).isoformat(),
                }
            )

    write_csv(output / "patients.csv", patients)
    write_csv(output / "encounters.csv", encounters)
    write_csv(output / "conditions.csv", conditions)
    write_csv(output / "medications.csv", medications)
    write_csv(output / "vitals.csv", vitals)
    write_csv(output / "clinical_notes.csv", notes)
    write_csv(output / "claims.csv", claims)
    write_csv(output / "care_tasks.csv", care_tasks or [{"task_id": "T0000", "patient_id": "P0000", "risk_tier": "Low", "status": "None", "assigned_role": "None", "due_date": ""}])

    print(f"Wrote synthetic datasets to {output}")


if __name__ == "__main__":
    main()

