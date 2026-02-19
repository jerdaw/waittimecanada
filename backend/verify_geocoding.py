import os
import sys

# ruff: noqa: E402, T201

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from waittime.services.geocoding import GeocodingService


def verify():
    service = GeocodingService()

    test_cases = [
        ("ca-on-sunnybrook", "Sunnybrook Health Sciences Centre"),
        ("ca-on-tor-east-hlth-ntwrk-michael-garron-hosp", "Michael Garron Hospital"),
        ("ca-on-ottawa-hospital-the-civic-site", "Ottawa Civic"),
        ("ca-on-niagara-health-system-marotta-family-hosp", "Marotta Family Hospital"),
        ("ca-on-thunder-bay-regional-hlth-sciences-ctr", "Thunder Bay Regional"),
    ]

    print(f"Loaded {len(service._manual_overrides)} overrides.")

    success_count = 0
    for hospital_id, name in test_cases:
        result = service.geocode_hospital(name, "ON", hospital_id=hospital_id)
        if result and result.latitude != 0.0:
            print(f"✅ {hospital_id}: ({result.latitude}, {result.longitude}) - {result.city}")
            success_count += 1
        else:
            print(f"❌ {hospital_id}: Failed or returned 0,0")

    # Check for junk data removal
    junk_id = "ca-on-202502"
    if junk_id not in service._manual_overrides:
        print(f"✅ Junk data '{junk_id}' successfully removed.")
    else:
        print(f"❌ Junk data '{junk_id}' still present!")

    if success_count == len(test_cases):
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print(f"\n{len(test_cases) - success_count} tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    verify()
