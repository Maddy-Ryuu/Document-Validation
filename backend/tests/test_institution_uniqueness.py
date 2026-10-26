import uuid
import threading
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.models import Institution, Application, AuditEvent

client = TestClient(app)


def test_01_duplicate_same_normalized_name_city_state_rejected():
    """Verify that creating an institution with the same normalized name, district/city, and state is rejected."""
    uid = uuid.uuid4().hex[:6].upper()
    base_payload = {
        "institution_identifier": f"AICTE-UNIQ-{uid}",
        "name": f"Himalayan Institute of Technology {uid}",
        "institution_type": "Engineering",
        "city": "Dehradun",
        "state": "Uttarakhand"
    }
    # First creation succeeds
    res1 = client.post("/api/institutions", json=base_payload)
    assert res1.status_code == 201

    # Second creation with identical location and name is rejected with 409 Conflict
    dup_payload = {
        "institution_identifier": f"AICTE-UNIQ-{uid}-DUP",
        "name": f"Himalayan Institute of Technology {uid}",
        "institution_type": "Engineering",
        "city": "Dehradun",
        "state": "Uttarakhand"
    }
    res2 = client.post("/api/institutions", json=dup_payload)
    assert res2.status_code == 409
    assert "already exists in Dehradun, Uttarakhand" in res2.json()["detail"]


def test_02_case_differences_and_extra_spaces_cannot_bypass():
    """Verify case differences and extra whitespace do not bypass duplicate detection."""
    uid = uuid.uuid4().hex[:6].upper()
    client.post("/api/institutions", json={
        "institution_identifier": f"AICTE-CASE-{uid}",
        "name": f"Sunrise Engineering College {uid}",
        "institution_type": "Engineering",
        "city": "Jaipur",
        "state": "Rajasthan"
    })

    # Attempt to bypass using leading/trailing spaces, multiple internal spaces, and lowercase/uppercase
    bypass_payload = {
        "institution_identifier": f"AICTE-CASE-{uid}-ALT",
        "name": f"   sunRISE    engineering   college   {uid}   ",
        "institution_type": "Engineering",
        "city": "  jaipur  ",
        "state": "  rajasthan  "
    }
    res = client.post("/api/institutions", json=bypass_payload)
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"].lower()


def test_03_same_name_in_different_district_permitted():
    """Verify the same institution name is permitted if the district/city is different."""
    uid = uuid.uuid4().hex[:6].upper()
    inst_name = f"Global Polytechnic Institute {uid}"

    # City 1: Nagpur
    res1 = client.post("/api/institutions", json={
        "institution_identifier": f"AICTE-DIFFCITY-1-{uid}",
        "name": inst_name,
        "institution_type": "Polytechnic",
        "city": "Nagpur",
        "state": "Maharashtra"
    })
    assert res1.status_code == 201

    # City 2: Nashik (Same state, different city/district)
    res2 = client.post("/api/institutions", json={
        "institution_identifier": f"AICTE-DIFFCITY-2-{uid}",
        "name": inst_name,
        "institution_type": "Polytechnic",
        "city": "Nashik",
        "state": "Maharashtra"
    })
    assert res2.status_code == 201
    assert res2.json()["city"] == "Nashik"


def test_04_same_name_in_different_state_permitted():
    """Verify the same institution name is permitted if the state is different."""
    uid = uuid.uuid4().hex[:6].upper()
    inst_name = f"National Academy of Management {uid}"

    # State 1: Karnataka
    res1 = client.post("/api/institutions", json={
        "institution_identifier": f"AICTE-DIFFST-1-{uid}",
        "name": inst_name,
        "institution_type": "Management",
        "city": "Belagavi",
        "state": "Karnataka"
    })
    assert res1.status_code == 201

    # State 2: Goa (Different state)
    res2 = client.post("/api/institutions", json={
        "institution_identifier": f"AICTE-DIFFST-2-{uid}",
        "name": inst_name,
        "institution_type": "Management",
        "city": "Panaji",
        "state": "Goa"
    })
    assert res2.status_code == 201
    assert res2.json()["state"] == "Goa"


def test_05_duplicate_official_aicte_identifier_rejected():
    """Verify that duplicate official AICTE identifiers are rejected regardless of location."""
    uid = uuid.uuid4().hex[:6].upper()
    official_code = f"AICTE-REG-{uid}"

    res1 = client.post("/api/institutions", json={
        "institution_identifier": official_code,
        "name": f"First College {uid}",
        "institution_type": "Engineering",
        "city": "Kochi",
        "state": "Kerala"
    })
    assert res1.status_code == 201

    # Same official code with different name and location
    res2 = client.post("/api/institutions", json={
        "institution_identifier": official_code,
        "name": f"Second College {uid}",
        "institution_type": "Pharmacy",
        "city": "Kozhikode",
        "state": "Kerala"
    })
    assert res2.status_code == 409
    assert f"official identifier '{official_code}' already exists" in res2.json()["detail"]


def test_06_updating_institute_cannot_create_duplicate():
    """Verify updating an institution's name/location or identifier to an existing one is rejected."""
    uid = uuid.uuid4().hex[:6].upper()

    # Institute A
    res_a = client.post("/api/institutions", json={
        "institution_identifier": f"AICTE-UPD-A-{uid}",
        "name": f"Institute Alpha {uid}",
        "institution_type": "Engineering",
        "city": "Bhopal",
        "state": "Madhya Pradesh"
    })
    assert res_a.status_code == 201
    inst_a_id = res_a.json()["id"]

    # Institute B
    res_b = client.post("/api/institutions", json={
        "institution_identifier": f"AICTE-UPD-B-{uid}",
        "name": f"Institute Beta {uid}",
        "institution_type": "Engineering",
        "city": "Bhopal",
        "state": "Madhya Pradesh"
    })
    assert res_b.status_code == 201
    inst_b_id = res_b.json()["id"]

    # Try to update Institute B's name to Institute Alpha in the same location
    res_upd = client.patch(f"/api/institutions/{inst_b_id}", json={
        "name": f"Institute Alpha {uid}"
    })
    assert res_upd.status_code == 409
    assert "already exists in Bhopal, Madhya Pradesh" in res_upd.json()["detail"]

    # Try to update Institute B's identifier to Institute A's identifier
    res_upd_id = client.patch(f"/api/institutions/{inst_b_id}", json={
        "institution_identifier": f"AICTE-UPD-A-{uid}"
    })
    assert res_upd_id.status_code == 409
    assert "official identifier" in res_upd_id.json()["detail"]

    # Updating Institute A with same data (no-op) or new non-colliding name succeeds
    res_upd_ok = client.patch(f"/api/institutions/{inst_a_id}", json={
        "name": f"Institute Alpha Renamed {uid}"
    })
    assert res_upd_ok.status_code == 200
    assert res_upd_ok.json()["name"] == f"Institute Alpha Renamed {uid}"


def test_07_concurrent_creation_cannot_bypass_database_constraint():
    """Verify that concurrent requests attempting to create identical institutions cannot bypass the constraint."""
    uid = uuid.uuid4().hex[:6].upper()
    payload = {
        "institution_identifier": f"AICTE-CONCUR-{uid}",
        "name": f"Concurrent Institute of Science {uid}",
        "institution_type": "Engineering",
        "city": "Chandigarh",
        "state": "Punjab"
    }

    results = []

    def attempt_create():
        c = TestClient(app)
        res = c.post("/api/institutions", json=payload)
        results.append(res.status_code)

    t1 = threading.Thread(target=attempt_create)
    t2 = threading.Thread(target=attempt_create)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exactly one thread should succeed (201), and the other must be rejected (409)
    assert 201 in results, f"Expected at least one 201, got {results}"
    assert 409 in results, f"Expected concurrent collision to be rejected with 409, got {results}"


def test_08_linked_records_and_audit_history_preserved():
    """Verify that canonical merged institute retains all linked applications and audit records."""
    db = SessionLocal()
    try:
        # Check canonical record exists and has linked applications
        canonical = db.query(Institution).filter(
            Institution.name.ilike("%Apex Institute of Technology & Advanced Studies%")
        ).first()
        assert canonical is not None
        assert len(canonical.applications) >= 40, f"Expected >= 40 linked apps, got {len(canonical.applications)}"

        # Verify audit event for merge exists
        merge_audit = db.query(AuditEvent).filter(
            AuditEvent.action == "MERGE_DUPLICATE_INSTITUTION"
        ).first()
        assert merge_audit is not None
        assert merge_audit.entity_id == canonical.id
    finally:
        db.close()


def test_09_institution_and_application_workflows_continue_to_function():
    """Verify standard application creation and document workflow functions smoothly."""
    # List institutions
    list_res = client.get("/api/institutions")
    assert list_res.status_code == 200
    inst_id = list_res.json()["items"][0]["id"]

    # Create new application for institution
    app_res = client.post("/api/applications", json={
        "institution_id": inst_id,
        "application_category": "Extension of Approval (EoA)",
        "academic_year": "2026-2027"
    })
    assert app_res.status_code == 201
    new_app_id = app_res.json()["id"]

    # Detail view
    detail_res = client.get(f"/api/applications/{new_app_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == new_app_id
