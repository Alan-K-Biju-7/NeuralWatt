from app.core.security import create_access_token, get_current_user_id
from fastapi.security import HTTPAuthorizationCredentials


def test_jwt_round_trip_returns_user_id():
    token = create_access_token("user-123", "demo@example.com")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    assert get_current_user_id(credentials) == "user-123"
