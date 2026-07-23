# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
"""
Auth Pipeline E2E Verification Script
======================================
Hits live auth endpoints and checks the database after each step
to verify data is stored/returned correctly.

Steps:
  1. Register a new user  → verify user row in DB
  2. Login with that user → verify tokens + last_login updated
  3. Refresh the token    → verify new access token is valid
  4. Login with wrong password → verify 401 and DB unchanged
  5. Register duplicate email  → verify 400 and no duplicate row
  6. Cleanup: delete test user from DB
"""

import json
import requests
from sqlalchemy import create_engine, text

# ────────────────────────────────────────────
# Config
# ────────────────────────────────────────────
BASE_URL = "http://127.0.0.1:8000/api/v1"
DB_URL = "postgresql+psycopg2://postgres:postgres123@localhost:5432/file_mediation"

TEST_USER = {
    "username": "auth_pipeline_test",
    "email": "auth_pipeline_test@example.com",
    "first_name": "Pipeline",
    "last_name": "Tester",
    "password": "SecurePass123!",
    "role_id": 2,  # ADMIN role
}

engine = create_engine(DB_URL)
passed = 0
failed = 0


def db_query(sql, **params):
    """Run a read query and return rows as list of dicts."""
    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        cols = result.keys()
        return [dict(zip(cols, row)) for row in result.fetchall()]


def db_execute(sql, **params):
    """Run a write query."""
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


def cleanup():
    """Remove test user if it exists."""
    db_execute(
        "DELETE FROM users WHERE email = :email",
        email=TEST_USER["email"],
    )


# ────────────────────────────────────────────
# Pre-clean
# ────────────────────────────────────────────
print("\n--- Cleaning up any previous test user...")
cleanup()

# ────────────────────────────────────────────
# Step 1: REGISTER
# ────────────────────────────────────────────
print("\n" + "=" * 42)
print("STEP 1: Register a new user")
print("=" * 42)
resp = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
print(f"  HTTP {resp.status_code}")
print(f"  Response: {json.dumps(resp.json(), indent=2, default=str)}")

check("Status code is 200", resp.status_code == 200, f"got {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    check("Response has 'id'", "id" in data)
    check("Username matches", data.get("username") == TEST_USER["username"], data.get("username"))
    check("Email matches", data.get("email") == TEST_USER["email"], data.get("email"))
    check("is_active is True", data.get("is_active") is True)

    # DB verification
    print("\n  [DB] Verification:")
    rows = db_query(
        "SELECT id, username, email, hashed_password, role_id, is_active, first_name, last_name "
        "FROM users WHERE email = :email",
        email=TEST_USER["email"],
    )
    check("User exists in DB", len(rows) == 1, f"found {len(rows)} rows")

    if rows:
        db_user = rows[0]
        check("DB username correct", db_user["username"] == TEST_USER["username"])
        check("DB email correct", db_user["email"] == TEST_USER["email"])
        check("DB first_name correct", db_user["first_name"] == TEST_USER["first_name"])
        check("DB last_name correct", db_user["last_name"] == TEST_USER["last_name"])
        check("DB role_id correct", db_user["role_id"] == TEST_USER["role_id"], f"got {db_user['role_id']}")
        check("DB password is hashed (not plain)", db_user["hashed_password"] != TEST_USER["password"])
        check("DB password starts with bcrypt prefix", db_user["hashed_password"].startswith("$2"))
        check("DB is_active is True", db_user["is_active"] is True)
        test_user_id = db_user["id"]

# ────────────────────────────────────────────
# Step 2: LOGIN
# ────────────────────────────────────────────
print("\n" + "=" * 42)
print("STEP 2: Login with registered user")
print("=" * 42)
login_payload = {
    "email": TEST_USER["email"],
    "password": TEST_USER["password"],
}
resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
print(f"  HTTP {resp.status_code}")
print(f"  Response: {json.dumps(resp.json(), indent=2, default=str)}")

check("Status code is 200", resp.status_code == 200, f"got {resp.status_code}")

access_token = None
refresh_token = None

if resp.status_code == 200:
    data = resp.json()
    check("Response has 'access_token'", "access_token" in data)
    check("Response has 'refresh_token'", "refresh_token" in data)
    check("token_type is 'bearer'", data.get("token_type") == "bearer", data.get("token_type"))
    check("user_id matches", data.get("user_id") == test_user_id, f"got {data.get('user_id')}")
    check("email matches", data.get("email") == TEST_USER["email"])
    check("username matches", data.get("username") == TEST_USER["username"])
    check("role is 'ADMIN'", data.get("role") == "ADMIN", data.get("role"))

    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")

    # Decode and verify JWT contents
    from jose import jwt
    decoded = jwt.decode(access_token, "7d4f2a91b8e34c5f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a9b8c7d6e5", algorithms=["HS256"])
    print(f"\n  [JWT] Decoded access token: {json.dumps(decoded, indent=2, default=str)}")
    check("JWT user_id matches", decoded.get("user_id") == test_user_id)
    check("JWT email matches", decoded.get("email") == TEST_USER["email"])
    check("JWT role is 'ADMIN'", decoded.get("role") == "ADMIN")
    check("JWT has expiry", "exp" in decoded)

    # DB verification: last_login should be updated
    print("\n  [DB] Verification:")
    rows = db_query(
        "SELECT last_login FROM users WHERE email = :email",
        email=TEST_USER["email"],
    )
    if rows:
        check("last_login is set after login", rows[0]["last_login"] is not None)

# ────────────────────────────────────────────
# Step 3: REFRESH TOKEN
# ────────────────────────────────────────────
print("\n" + "=" * 42)
print("STEP 3: Refresh token")
print("=" * 42)
if refresh_token:
    resp = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": refresh_token})
    print(f"  HTTP {resp.status_code}")
    print(f"  Response: {json.dumps(resp.json(), indent=2, default=str)}")

    check("Status code is 200", resp.status_code == 200, f"got {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        check("New access_token returned", "access_token" in data and data["access_token"])
        check("New token differs from old", data["access_token"] != access_token, "same token returned")
        check("refresh_token echoed back", data.get("refresh_token") == refresh_token)
        check("token_type is 'bearer'", data.get("token_type") == "bearer")

        # Verify new token is valid JWT
        from jose import jwt
        new_decoded = jwt.decode(
            data["access_token"],
            "7d4f2a91b8e34c5f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a9b8c7d6e5",
            algorithms=["HS256"],
        )
        check("New JWT has same user_id", new_decoded.get("user_id") == test_user_id)
        check("New JWT has same email", new_decoded.get("email") == TEST_USER["email"])
else:
    print("  [WARN] Skipped -- no refresh token from login step")

# ────────────────────────────────────────────
# Step 4: LOGIN with WRONG PASSWORD
# ────────────────────────────────────────────
print("\n" + "=" * 42)
print("STEP 4: Login with wrong password")
print("=" * 42)
resp = requests.post(f"{BASE_URL}/auth/login", json={
    "email": TEST_USER["email"],
    "password": "WrongPassword99!",
})
print(f"  HTTP {resp.status_code}")
print(f"  Response: {json.dumps(resp.json(), indent=2, default=str)}")
check("Status code is 401", resp.status_code == 401, f"got {resp.status_code}")

# ────────────────────────────────────────────
# Step 5: REGISTER DUPLICATE EMAIL
# ────────────────────────────────────────────
print("\n" + "=" * 42)
print("STEP 5: Register with duplicate email")
print("=" * 42)
dup_user = {**TEST_USER, "username": "different_username"}
resp = requests.post(f"{BASE_URL}/auth/register", json=dup_user)
print(f"  HTTP {resp.status_code}")
print(f"  Response: {json.dumps(resp.json(), indent=2, default=str)}")
check("Status code is 400", resp.status_code == 400, f"got {resp.status_code}")
check("Error says 'Email already exists'", "Email already exists" in resp.json().get("detail", ""))

# DB verification: still only 1 user with this email
rows = db_query(
    "SELECT count(*) as cnt FROM users WHERE email = :email",
    email=TEST_USER["email"],
)
check("DB still has exactly 1 user with this email", rows[0]["cnt"] == 1, f"found {rows[0]['cnt']}")

# ────────────────────────────────────────────
# Step 6: REFRESH with INVALID TOKEN
# ────────────────────────────────────────────
print("\n" + "=" * 42)
print("STEP 6: Refresh with invalid token")
print("=" * 42)
resp = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": "invalid.token.here"})
print(f"  HTTP {resp.status_code}")
print(f"  Response: {json.dumps(resp.json(), indent=2, default=str)}")
check("Status code is 401", resp.status_code == 401, f"got {resp.status_code}")

# ────────────────────────────────────────────
# Step 7: LOGIN with NON-EXISTENT EMAIL
# ────────────────────────────────────────────
print("\n" + "=" * 42)
print("STEP 7: Login with non-existent email")
print("=" * 42)
resp = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "nonexistent@nowhere.com",
    "password": "SomePass12345!",
})
print(f"  HTTP {resp.status_code}")
print(f"  Response: {json.dumps(resp.json(), indent=2, default=str)}")
check("Status code is 401", resp.status_code == 401, f"got {resp.status_code}")

# ────────────────────────────────────────────
# Cleanup
# ────────────────────────────────────────────
print("\n--- Cleaning up test user from DB...")
cleanup()
rows = db_query("SELECT count(*) as cnt FROM users WHERE email = :email", email=TEST_USER["email"])
check("Test user removed from DB", rows[0]["cnt"] == 0)

# Summary
print("\n" + "=" * 42)
print(f"  RESULTS:  {passed} passed, {failed} failed")
print("=" * 42)

sys.exit(1 if failed else 0)
