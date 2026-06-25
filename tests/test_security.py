from app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_password_does_not_store_plaintext():
    hashed = hash_password("SuperSecret123")
    assert hashed != "SuperSecret123"
    assert verify_password("SuperSecret123", hashed)


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("SuperSecret123")
    assert not verify_password("WrongPassword", hashed)


def test_create_and_decode_access_token_roundtrip():
    token = create_access_token(subject="user@example.com", role="client")
    payload = decode_access_token(token)
    assert payload["sub"] == "user@example.com"
    assert payload["role"] == "client"


def test_decode_invalid_token_returns_none():
    assert decode_access_token("not-a-valid-jwt") is None


def test_decode_tampered_token_returns_none():
    token = create_access_token(subject="user@example.com", role="client")
    tampered = token[:-2] + "xx"
    assert decode_access_token(tampered) is None
