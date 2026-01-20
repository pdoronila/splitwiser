import os
from fastapi.testclient import TestClient
from main import app  # Changed from backend.main to main since PYTHONPATH=backend

client = TestClient(app)

def test_cors_rejects_evil_origin():
    """Verify that requests from unauthorized origins do not receive permissive CORS headers."""
    origin = "http://evil.com"
    headers = {"Origin": origin}

    response = client.get("/groups", headers=headers)

    # ACAO should NOT be http://evil.com and definitely not * if credentials are true
    acao = response.headers.get("access-control-allow-origin")
    acac = response.headers.get("access-control-allow-credentials")

    print(f"\nEvil Origin Test ({origin}):")
    print(f"ACAO: {acao}")
    print(f"ACAC: {acac}")

    # Starlette CORSMiddleware behavior: if origin is not allowed, it doesn't send ACAO/ACAC
    assert acao != origin, "Vulnerability: Arbitrary origin reflected in Access-Control-Allow-Origin"
    assert acao != "*", "Vulnerability: Wildcard origin allowed with credentials"

def test_cors_allows_valid_origin():
    """Verify that requests from whitelisted origins receive correct CORS headers."""
    # Assuming default localhost:3000 is in the whitelist
    origin = "http://localhost:3000"
    headers = {"Origin": origin}

    response = client.get("/groups", headers=headers)

    acao = response.headers.get("access-control-allow-origin")
    acac = response.headers.get("access-control-allow-credentials")

    print(f"\nValid Origin Test ({origin}):")
    print(f"ACAO: {acao}")
    print(f"ACAC: {acac}")

    assert acao == origin, "Valid origin was not allowed"
    assert acac == "true", "Credentials not allowed for valid origin"

if __name__ == "__main__":
    test_cors_rejects_evil_origin()
    test_cors_allows_valid_origin()
    print("\n[+] All CORS security tests passed.")
