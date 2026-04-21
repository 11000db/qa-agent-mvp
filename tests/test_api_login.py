import requests
import pytest

BASE_URL = "https://dummyjson.com"

class TestLoginAPI:

    def test_login_success(self):
        """POST /auth/login - 정상 로그인"""
        payload = {
            "username": "emilys",
            "password": "emilyspass"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data
        assert data["username"] == "emilys"

    def test_login_wrong_password(self):
        """POST /auth/login - 잘못된 비밀번호 (Negative)"""
        payload = {
            "username": "emilys",
            "password": "wrongpassword"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        assert response.status_code == 400

    def test_login_missing_username(self):
        """POST /auth/login - username 누락 (Negative)"""
        payload = {"password": "emilyspass"}
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        assert response.status_code == 400

    def test_login_missing_password(self):
        """POST /auth/login - password 누락 (Negative)"""
        payload = {"username": "emilys"}
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        assert response.status_code == 400

    def test_login_empty_body(self):
        """POST /auth/login - 빈 요청 (Negative)"""
        response = requests.post(f"{BASE_URL}/auth/login", json={})
        assert response.status_code == 400

    def test_login_response_structure(self):
        """POST /auth/login - 응답 구조 검증"""
        payload = {
            "username": "emilys",
            "password": "emilyspass"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data
        assert "refreshToken" in data
        assert "id" in data
        assert "email" in data