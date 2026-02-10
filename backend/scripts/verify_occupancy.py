import sys
from waittime.core import Measurement, MetricFamily, StartEvent, EndEvent, StatisticType, PatientScope
from waittime.services.database import DatabaseService

def test_occupancy():
    print("Testing occupancy columns...")
    db = DatabaseService()
    print(f"DB URL: {db.database_url.split('@')[1] if '@' in db.database_url else 'LOCAL'}")

    # Create a dummy measurement with occupancy data
    m = Measurement(
        hospital_id="ca-on-toronto-general",
        value=123.0,
        metric_family=MetricFamily.TIME_TO_PROVIDER,
        start_event=StartEvent.TRIAGE,
        end_event=EndEvent.PHYSICIAN,
        statistic_type=StatisticType.MEAN,
        patient_scope=PatientScope.ALL,
        source_id="ontario-health",
        raw_payload_hash="a" * 64,
        patients_waiting=10,
        patients_in_treatment=5,
        total_treatment_spaces=50
    )

    try:
        inserted = db.insert_measurement(m)
        print(f"Inserted: ID={inserted.get('id')}, Waiting={inserted.get('patients_waiting')}")

        if inserted.get('patients_waiting') != 10:
            print("ERROR: patients_waiting mismatch")
            sys.exit(1)

        if inserted.get('patients_in_treatment') != 5:
            print("ERROR: patients_in_treatment mismatch")
            sys.exit(1)

        # Retrieve it back to be sure
        fetched = db.get_latest_measurement("ca-on-toronto-general")
        if fetched and fetched.patients_waiting == 10:
             print("✅ Verification Successful: Occupancy data round-tripped.")
        else:
             print("❌ Verification Failed: Could not retrieve occupancy data.")
             sys.exit(1)

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_occupancy()
