# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
"""
Endpoint Verification Script
=============================
Hits live endpoints and checks the database after each step.

Endpoints tested:
  1. POST /api/v1/filtering/evaluate
  2. POST /api/v1/pipelines          (auth required)
  3. GET  /api/v1/pipelines
  4. GET  /api/v1/pipelines/{id}
  5. PUT  /api/v1/pipelines/{id}
  6. DELETE /api/v1/pipelines/{id}
  7. POST /api/v1/transformations/execute
"""

import json
import time
import requests
from sqlalchemy import create_engine, text

# ── Config ──────────────────────────────────
BASE_URL = "http://127.0.0.1:8000/api/v1"
DB_URL = "postgresql+psycopg2://postgres:postgres123@localhost:5432/file_mediation"

engine = create_engine(DB_URL)
passed = 0
failed = 0


def db_query(sql, **params):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        cols = result.keys()
        return [dict(zip(cols, row)) for row in result.fetchall()]


def db_execute(sql, **params):
    with engine.connect() as conn:
        conn.execute(text(sql), params)
        conn.commit()


def check(label, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  [PASS] {label}")
        passed += 1
    else:
        print(f"  [FAIL] {label}  ->  {detail}")
        failed += 1


def section(title):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")


# ── Cleanup any previous test data ──────────
def cleanup():
    # Delete in FK order: pipelines -> sources/destinations -> users
    db_execute("DELETE FROM pipelines WHERE name LIKE 'verify_test_%'")
    db_execute("DELETE FROM sources WHERE name = 'verify_test_source'")
    db_execute("DELETE FROM destinations WHERE name = 'verify_test_dest'")
    db_execute("DELETE FROM users WHERE email = 'verify_endpoint@example.com'")


print("\n--- Pre-cleaning test data...")
cleanup()


# ── SETUP: Register + Login to get auth token ──
section("SETUP: Register + Login for auth token")

TEST_USER = {
    "username": "verify_ep_user",
    "email": "verify_endpoint@example.com",
    "first_name": "Verify",
    "last_name": "Tester",
    "password": "SecurePass123!",
    "role_id": 2,
}

resp = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
print(f"  Register: HTTP {resp.status_code}")
check("User registered", resp.status_code == 200, f"got {resp.status_code}: {resp.text}")

resp = requests.post(f"{BASE_URL}/auth/login", json={
    "email": TEST_USER["email"],
    "password": TEST_USER["password"],
})
print(f"  Login: HTTP {resp.status_code}")
check("Login successful", resp.status_code == 200, f"got {resp.status_code}: {resp.text}")

AUTH_HEADERS = {}
test_user_id = None
if resp.status_code == 200:
    token = resp.json()["access_token"]
    test_user_id = resp.json()["user_id"]
    AUTH_HEADERS = {"Authorization": f"Bearer {token}"}
    print(f"  Got token for user_id={test_user_id}")


# ── SETUP: Seed Source + Destination directly in DB ──
section("SETUP: Seed Source and Destination in DB")

db_execute("""
    INSERT INTO sources (name, source_type, config, is_active, created_at, updated_at)
    VALUES ('verify_test_source', 'LOCAL',
            '{"type": "LOCAL", "source_path": "/tmp/src", "archive_path": "/tmp/arc", "rejected_path": "/tmp/rej", "allowed_extensions": [".csv"]}'::jsonb,
            true, NOW(), NOW())
""")
db_execute("""
    INSERT INTO destinations (name, destination_type, config, is_active, created_at, updated_at)
    VALUES ('verify_test_dest', 'LOCAL',
            '{"destination_directory": "/tmp/dest"}'::jsonb,
            true, NOW(), NOW())
""")

source_rows = db_query("SELECT id FROM sources WHERE name = 'verify_test_source'")
dest_rows = db_query("SELECT id FROM destinations WHERE name = 'verify_test_dest'")
check("Source seeded in DB", len(source_rows) == 1)
check("Destination seeded in DB", len(dest_rows) == 1)

source_id = source_rows[0]["id"] if source_rows else None
dest_id = dest_rows[0]["id"] if dest_rows else None
print(f"  source_id={source_id}, destination_id={dest_id}")


# ============================================================
# STEP 1: POST /api/v1/filtering/evaluate
# ============================================================
section("STEP 1: POST /filtering/evaluate")

filter_payload = {
    "records": [
        {"name": "Alice", "age": 30, "status": "ACTIVE"},
        {"name": "Bob", "age": 17, "status": "INACTIVE"},
        {"name": "Charlie", "age": 25, "status": "ACTIVE"},
        {"name": "Diana", "age": 45, "status": "ACTIVE"},
    ],
    "rules": [
        {"field_name": "status", "operator": "=", "value": "ACTIVE"},
        {"field_name": "age", "operator": ">=", "value": 18},
    ]
}

resp = requests.post(f"{BASE_URL}/filtering/evaluate", json=filter_payload)
print(f"  HTTP {resp.status_code}")
data = resp.json()
print(f"  Response: {json.dumps(data, indent=2, default=str)}")

check("Status code is 200", resp.status_code == 200, f"got {resp.status_code}")

if resp.status_code == 200:
    stats = data.get("statistics", {})
    check("total_records is 4", stats.get("total_records") == 4, stats.get("total_records"))
    check("accepted_records is 3", stats.get("accepted_records") == 3, stats.get("accepted_records"))
    check("rejected_records is 1", stats.get("rejected_records") == 1, stats.get("rejected_records"))

    accepted = data.get("accepted_records", [])
    accepted_names = [r["name"] for r in accepted]
    check("Alice accepted", "Alice" in accepted_names, accepted_names)
    check("Charlie accepted", "Charlie" in accepted_names, accepted_names)
    check("Diana accepted", "Diana" in accepted_names, accepted_names)

    rejected = data.get("rejected_records", [])
    check("1 rejected record (Bob)", len(rejected) == 1, len(rejected))
    if rejected:
        check("Rejected record is Bob", rejected[0]["original_record"]["name"] == "Bob")


# ============================================================
# STEP 2: POST /api/v1/pipelines (create - auth required)
# ============================================================
section("STEP 2: POST /pipelines (create)")

pipeline_payload = {
    "name": "verify_test_pipeline_01",
    "description": "Test pipeline for endpoint verification",
    "source_id": source_id,
    "destination_id": dest_id,
    "decoder_type": "CSV",
    "output_format": "CSV",
    "archive_enabled": True,
    "retry_count": 3,
}

# First: try without auth -- should fail
resp_no_auth = requests.post(f"{BASE_URL}/pipelines", json=pipeline_payload)
print(f"  Without auth: HTTP {resp_no_auth.status_code}")
check("Create without auth returns 401", resp_no_auth.status_code == 401, f"got {resp_no_auth.status_code}")

# Now with auth
resp = requests.post(f"{BASE_URL}/pipelines", json=pipeline_payload, headers=AUTH_HEADERS)
print(f"  With auth: HTTP {resp.status_code}")
print(f"  Response: {json.dumps(resp.json(), indent=2, default=str)}")

check("Status code is 200", resp.status_code == 200, f"got {resp.status_code}")

created_pipeline_id = None
if resp.status_code == 200:
    data = resp.json()
    created_pipeline_id = data.get("id")
    check("Response has 'id'", created_pipeline_id is not None)
    check("Name matches", data.get("name") == pipeline_payload["name"])
    check("source_id matches", data.get("source_id") == source_id)
    check("destination_id matches", data.get("destination_id") == dest_id)
    check("decoder_type is CSV", data.get("decoder_type") == "CSV")
    check("is_active is True", data.get("is_active") is True)
    check("created_by_id matches user", data.get("created_by_id") == test_user_id, data.get("created_by_id"))

    # DB verification
    print("\n  [DB] Verification:")
    rows = db_query(
        "SELECT id, name, source_id, destination_id, decoder_type, is_active, created_by_id "
        "FROM pipelines WHERE id = :pid",
        pid=created_pipeline_id,
    )
    check("Pipeline exists in DB", len(rows) == 1)
    if rows:
        db_pipe = rows[0]
        check("DB name correct", db_pipe["name"] == pipeline_payload["name"])
        check("DB source_id correct", db_pipe["source_id"] == source_id)
        check("DB destination_id correct", db_pipe["destination_id"] == dest_id)
        check("DB decoder_type correct", db_pipe["decoder_type"] == "CSV")
        check("DB is_active is True", db_pipe["is_active"] is True)
        check("DB created_by_id matches", db_pipe["created_by_id"] == test_user_id)

# Try duplicate name
resp_dup = requests.post(f"{BASE_URL}/pipelines", json=pipeline_payload, headers=AUTH_HEADERS)
print(f"\n  Duplicate name: HTTP {resp_dup.status_code}")
check("Duplicate name returns 400", resp_dup.status_code == 400, f"got {resp_dup.status_code}")


# ============================================================
# STEP 3: GET /api/v1/pipelines (list all)
# ============================================================
section("STEP 3: GET /pipelines (list all)")

resp = requests.get(f"{BASE_URL}/pipelines")
print(f"  HTTP {resp.status_code}")
data = resp.json()

check("Status code is 200", resp.status_code == 200, f"got {resp.status_code}")
check("Response is a list", isinstance(data, list), type(data).__name__)
check("At least 1 pipeline in list", len(data) >= 1, len(data))

# Find our test pipeline in the list
our_pipeline = [p for p in data if p.get("id") == created_pipeline_id]
check("Our test pipeline is in the list", len(our_pipeline) == 1)

if our_pipeline:
    p = our_pipeline[0]
    check("Listed pipeline name matches", p["name"] == pipeline_payload["name"])
    check("Listed pipeline has created_at", "created_at" in p)


# ============================================================
# STEP 4: GET /api/v1/pipelines/{id} (get by id)
# ============================================================
section("STEP 4: GET /pipelines/{id}")

resp = requests.get(f"{BASE_URL}/pipelines/{created_pipeline_id}")
print(f"  HTTP {resp.status_code}")
data = resp.json()
print(f"  Response: {json.dumps(data, indent=2, default=str)}")

check("Status code is 200", resp.status_code == 200, f"got {resp.status_code}")

if resp.status_code == 200:
    check("id matches", data.get("id") == created_pipeline_id)
    check("name matches", data.get("name") == pipeline_payload["name"])
    check("description matches", data.get("description") == pipeline_payload["description"])
    check("source_id matches", data.get("source_id") == source_id)
    check("decoder_type matches", data.get("decoder_type") == "CSV")

# Non-existent ID
resp_404 = requests.get(f"{BASE_URL}/pipelines/99999")
print(f"  Non-existent ID: HTTP {resp_404.status_code}")
check("Non-existent pipeline returns 404", resp_404.status_code == 404, f"got {resp_404.status_code}")


# ============================================================
# STEP 5: PUT /api/v1/pipelines/{id} (update)
# ============================================================
section("STEP 5: PUT /pipelines/{id} (update)")

update_payload = {
    "name": "verify_test_pipeline_updated",
    "description": "Updated description",
    "retry_count": 5,
    "is_active": False,
}

resp = requests.put(f"{BASE_URL}/pipelines/{created_pipeline_id}", json=update_payload)
print(f"  HTTP {resp.status_code}")
data = resp.json()
print(f"  Response: {json.dumps(data, indent=2, default=str)}")

check("Status code is 200", resp.status_code == 200, f"got {resp.status_code}")

if resp.status_code == 200:
    check("Name updated", data.get("name") == "verify_test_pipeline_updated")
    check("Description updated", data.get("description") == "Updated description")
    check("retry_count updated to 5", data.get("retry_count") == 5, data.get("retry_count"))
    check("is_active updated to False", data.get("is_active") is False, data.get("is_active"))
    # Fields not sent should remain unchanged
    check("source_id unchanged", data.get("source_id") == source_id)
    check("decoder_type unchanged", data.get("decoder_type") == "CSV")

    # DB verification
    print("\n  [DB] Verification:")
    rows = db_query(
        "SELECT name, description, retry_count, is_active FROM pipelines WHERE id = :pid",
        pid=created_pipeline_id,
    )
    if rows:
        db_pipe = rows[0]
        check("DB name updated", db_pipe["name"] == "verify_test_pipeline_updated")
        check("DB description updated", db_pipe["description"] == "Updated description")
        check("DB retry_count is 5", db_pipe["retry_count"] == 5, db_pipe["retry_count"])
        check("DB is_active is False", db_pipe["is_active"] is False, db_pipe["is_active"])


# ============================================================
# STEP 6: DELETE /api/v1/pipelines/{id}
# ============================================================
section("STEP 6: DELETE /pipelines/{id}")

resp = requests.delete(f"{BASE_URL}/pipelines/{created_pipeline_id}")
print(f"  HTTP {resp.status_code}")
data = resp.json()
print(f"  Response: {json.dumps(data, indent=2, default=str)}")

check("Status code is 200", resp.status_code == 200, f"got {resp.status_code}")
check("Message says deleted", "deleted" in data.get("message", "").lower(), data.get("message"))

# DB verification
print("\n  [DB] Verification:")
rows = db_query("SELECT id FROM pipelines WHERE id = :pid", pid=created_pipeline_id)
check("Pipeline removed from DB", len(rows) == 0, f"still found {len(rows)} rows")

# Trying to get deleted pipeline
resp_gone = requests.get(f"{BASE_URL}/pipelines/{created_pipeline_id}")
print(f"  GET after delete: HTTP {resp_gone.status_code}")
check("GET deleted pipeline returns 404", resp_gone.status_code == 404, f"got {resp_gone.status_code}")

# Delete non-existent
resp_404 = requests.delete(f"{BASE_URL}/pipelines/99999")
print(f"  Delete non-existent: HTTP {resp_404.status_code}")
check("Delete non-existent returns 404", resp_404.status_code == 404, f"got {resp_404.status_code}")


# ============================================================
# STEP 7: POST /api/v1/transformations/execute
# ============================================================
section("STEP 7: POST /transformations/execute")

transform_payload = {
    "records": [
        {"id": "101", "full_name": "Alice Smith", "dob": "1995-06-15", "is_premium": "true", "balance": "1250.50"},
        {"id": "102", "full_name": "Bob Jones", "dob": "1988-03-22", "is_premium": "false", "balance": "340.00"},
        {"id": "103", "full_name": "Charlie Brown", "dob": "2001-11-08", "is_premium": "yes", "balance": "5600.75"},
    ],
    "mappings": [
        {
            "source_field": "id",
            "target_field": "user_id",
            "transformation_type": "COPY",
            "required": True,
        },
        {
            "source_field": "full_name",
            "target_field": "name",
            "transformation_type": "COPY",
            "required": True,
        },
        {
            "source_field": "is_premium",
            "target_field": "premium_flag",
            "transformation_type": "BOOLEAN_CONVERSION",
            "required": False,
        },
        {
            "source_field": "balance",
            "target_field": "account_balance",
            "transformation_type": "NUMBER_FORMAT",
            "required": False,
        },
    ],
}

resp = requests.post(f"{BASE_URL}/transformations/execute", json=transform_payload)
print(f"  HTTP {resp.status_code}")
data = resp.json()
print(f"  Response: {json.dumps(data, indent=2, default=str)}")

check("Status code is 200", resp.status_code == 200, f"got {resp.status_code}")

if resp.status_code == 200:
    stats = data.get("statistics", {})
    check("total_records is 3", stats.get("total_records") == 3, stats.get("total_records"))
    check("transformed_records count", stats.get("transformed_records") == 3, stats.get("transformed_records"))
    check("rejected_records is 0", stats.get("rejected_records") == 0, stats.get("rejected_records"))

    transformed = data.get("transformed_records", [])
    check("3 transformed records returned", len(transformed) == 3, len(transformed))

    if transformed:
        alice = transformed[0]
        check("Alice user_id is '101'", alice.get("user_id") == "101", alice.get("user_id"))
        check("Alice name is 'Alice Smith'", alice.get("name") == "Alice Smith", alice.get("name"))
        check("Alice has premium_flag", "premium_flag" in alice, list(alice.keys()))
        check("Alice has account_balance", "account_balance" in alice, list(alice.keys()))

# Test with empty records
resp_empty = requests.post(f"{BASE_URL}/transformations/execute", json={
    "records": [],
    "mappings": [{"source_field": "a", "target_field": "b", "transformation_type": "COPY"}],
})
print(f"\n  Empty records: HTTP {resp_empty.status_code}")
check("Empty records returns 200", resp_empty.status_code == 200, f"got {resp_empty.status_code}")
if resp_empty.status_code == 200:
    check("Empty records -> 0 transformed", resp_empty.json()["statistics"]["total_records"] == 0)


# ============================================================
# CLEANUP
# ============================================================
section("CLEANUP")
cleanup()

rows = db_query("SELECT count(*) as cnt FROM pipelines WHERE name LIKE 'verify_test_%'")
check("Test pipelines cleaned up", rows[0]["cnt"] == 0)
rows = db_query("SELECT count(*) as cnt FROM sources WHERE name = 'verify_test_source'")
check("Test source cleaned up", rows[0]["cnt"] == 0)
rows = db_query("SELECT count(*) as cnt FROM destinations WHERE name = 'verify_test_dest'")
check("Test destination cleaned up", rows[0]["cnt"] == 0)
rows = db_query("SELECT count(*) as cnt FROM users WHERE email = 'verify_endpoint@example.com'")
check("Test user cleaned up", rows[0]["cnt"] == 0)


# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'=' * 50}")
print(f"  RESULTS:  {passed} passed, {failed} failed")
print(f"{'=' * 50}")

sys.exit(1 if failed else 0)
