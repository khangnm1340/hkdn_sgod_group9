import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        email="testuser@example.com",
        password="ValidPassword123!",
        first_name="Nguyen",
        last_name="Van A",
    )


@pytest.fixture
def auth_client(test_user):
    client = APIClient()
    response = client.post(
        "/api/v1/auth/token/",
        {"email": "testuser@example.com", "password": "ValidPassword123!"},
        format="json",
    )
    access_token = response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return client, response.data


# ==============================================================================
# FR-01: Đăng ký tài khoản mới (/api/v1/auth/register/)
# ==============================================================================

@pytest.mark.django_db
def test_register_success(api_client):
    payload = {
        "email": "newuser@example.com",
        "password": "SecurePassword123!",
        "first_name": "Tran",
        "last_name": "Van B",
    }
    response = api_client.post("/api/v1/auth/register/", payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    data = response.data
    assert "id" in data
    assert uuid.UUID(str(data["id"]))  # UUIDv4 validation
    assert data["email"] == "newuser@example.com"
    assert data["first_name"] == "Tran"
    assert data["last_name"] == "Van B"
    assert data["message"] == "Đăng ký tài khoản thành công"

    # Verify user saved in DB with hashed password
    user = User.objects.get(email="newuser@example.com")
    assert user.check_password("SecurePassword123!")


@pytest.mark.django_db
def test_register_duplicate_email(api_client, test_user):
    payload = {
        "email": "testuser@example.com",
        "password": "SecurePassword123!",
        "first_name": "Duplicate",
        "last_name": "User",
    }
    response = api_client.post("/api/v1/auth/register/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


@pytest.mark.django_db
def test_register_invalid_data(api_client):
    # Missing email
    response = api_client.post(
        "/api/v1/auth/register/",
        {"password": "Short"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==============================================================================
# FR-02: Đăng nhập hệ thống (/api/v1/auth/token/)
# ==============================================================================

@pytest.mark.django_db
def test_login_success(api_client, test_user):
    payload = {
        "email": "testuser@example.com",
        "password": "ValidPassword123!",
    }
    response = api_client.post("/api/v1/auth/token/", payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert "access" in data
    assert "refresh" in data
    assert "user" in data
    assert data["user"]["id"] == str(test_user.id)
    assert data["user"]["email"] == "testuser@example.com"
    assert data["user"]["first_name"] == "Nguyen"
    assert data["user"]["last_name"] == "Van A"


@pytest.mark.django_db
def test_login_invalid_credentials(api_client, test_user):
    payload = {
        "email": "testuser@example.com",
        "password": "WrongPassword123!",
    }
    response = api_client.post("/api/v1/auth/token/", payload, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==============================================================================
# FR-04: Làm mới Token (/api/v1/auth/token/refresh/)
# ==============================================================================

@pytest.mark.django_db
def test_refresh_token_success(api_client, test_user):
    # First login to get refresh token
    login_res = api_client.post(
        "/api/v1/auth/token/",
        {"email": "testuser@example.com", "password": "ValidPassword123!"},
        format="json",
    )
    refresh_token = login_res.data["refresh"]

    # Refresh
    response = api_client.post(
        "/api/v1/auth/token/refresh/",
        {"refresh": refresh_token},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


# ==============================================================================
# FR-05, FR-06, FR-07: Hồ sơ cá nhân (/api/v1/auth/me/)
# ==============================================================================

@pytest.mark.django_db
def test_get_me_authenticated(auth_client, test_user):
    client, _ = auth_client
    response = client.get("/api/v1/auth/me/")
    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert data["id"] == str(test_user.id)
    assert data["email"] == "testuser@example.com"
    assert data["first_name"] == "Nguyen"
    assert data["last_name"] == "Van A"
    assert data["is_active"] is True
    assert "date_joined" in data


@pytest.mark.django_db
def test_get_me_unauthenticated(api_client):
    response = api_client.get("/api/v1/auth/me/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ==============================================================================
# FR-08: Cập nhật hồ sơ cá nhân (PATCH /api/v1/auth/me/)
# ==============================================================================

@pytest.mark.django_db
def test_update_me(auth_client, test_user):
    client, _ = auth_client
    payload = {
        "first_name": "Nguyen Updated",
        "last_name": "Van B",
    }
    response = client.patch("/api/v1/auth/me/", payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "Nguyen Updated"
    assert response.data["last_name"] == "Van B"

    test_user.refresh_from_db()
    assert test_user.first_name == "Nguyen Updated"
    assert test_user.last_name == "Van B"


# ==============================================================================
# FR-09: Đổi mật khẩu (/api/v1/auth/change-password/)
# ==============================================================================

@pytest.mark.django_db
def test_change_password_success(auth_client, test_user, api_client):
    client, _ = auth_client
    payload = {
        "old_password": "ValidPassword123!",
        "new_password": "BrandNewPassword789!",
    }
    response = client.post("/api/v1/auth/change-password/", payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["detail"] == "Đổi mật khẩu thành công."

    # Login with new password should succeed
    login_new = api_client.post(
        "/api/v1/auth/token/",
        {"email": "testuser@example.com", "password": "BrandNewPassword789!"},
        format="json",
    )
    assert login_new.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_change_password_wrong_old_password(auth_client):
    client, _ = auth_client
    payload = {
        "old_password": "IncorrectPassword999!",
        "new_password": "BrandNewPassword789!",
    }
    response = client.post("/api/v1/auth/change-password/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ==============================================================================
# FR-03: Đăng xuất & Token Blacklist (/api/v1/auth/logout/)
# ==============================================================================

@pytest.mark.django_db
def test_logout_and_blacklist_token(auth_client, api_client):
    client, token_data = auth_client
    refresh_token = token_data["refresh"]

    # Logout
    logout_res = client.post(
        "/api/v1/auth/logout/",
        {"refresh": refresh_token},
        format="json",
    )
    assert logout_res.status_code == status.HTTP_200_OK
    assert logout_res.data["detail"] == "Đăng xuất thành công."

    # Attempt to refresh with blacklisted token should fail
    refresh_res = api_client.post(
        "/api/v1/auth/token/refresh/",
        {"refresh": refresh_token},
        format="json",
    )
    assert refresh_res.status_code == status.HTTP_401_UNAUTHORIZED
