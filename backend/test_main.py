import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# 회원가입/로그인/내 정보 테스트

def test_signup():
    data = {
        "email": "testuser1@example.com",
        "password": "testpass1",
        "name": "테스트유저1",
        "role": "mentee"
    }
    r = client.post("/api/signup", json=data)
    assert r.status_code in (201, 400)

def test_login():
    data = {"email": "testuser1@example.com", "password": "testpass1"}
    r = client.post("/api/login", json=data)
    assert r.status_code == 200
    assert "token" in r.json()
    return r.json()["token"]

def test_me():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/me", headers=headers)
    assert r.status_code == 200
    assert "email" in r.json()
    assert "role" in r.json()

def test_update_profile():
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "id": 1,
        "name": "테스트유저1수정",
        "role": "mentee",
        "bio": "수정된 소개",
        "image": "",
    }
    r = client.put("/api/profile", json=data, headers=headers)
    assert r.status_code in (200, 400)

def test_mentors_list():
    # 멘토 계정 생성 및 로그인
    mentor_signup = {
        "email": "mentor1@example.com",
        "password": "mentorpass1",
        "name": "멘토1",
        "role": "mentor"
    }
    client.post("/api/signup", json=mentor_signup)
    mentor_login = {"email": "mentor1@example.com", "password": "mentorpass1"}
    mentor_token = client.post("/api/login", json=mentor_login).json()["token"]
    # 멘티 로그인
    mentee_token = test_login()
    mentee_headers = {"Authorization": f"Bearer {mentee_token}"}
    r = client.get("/api/mentors", headers=mentee_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_match_request_flow():
    # 멘토 계정 생성 및 로그인
    mentor_signup = {
        "email": "mentor2@example.com",
        "password": "mentorpass2",
        "name": "멘토2",
        "role": "mentor"
    }
    client.post("/api/signup", json=mentor_signup)
    mentor_login = {"email": "mentor2@example.com", "password": "mentorpass2"}
    mentor_token = client.post("/api/login", json=mentor_login).json()["token"]
    mentor_headers = {"Authorization": f"Bearer {mentor_token}"}
    # 멘티 로그인
    mentee_token = test_login()
    mentee_headers = {"Authorization": f"Bearer {mentee_token}"}
    # 멘토 id 찾기
    mentors = client.get("/api/mentors", headers=mentee_headers).json()
    mentor_id = [m["id"] for m in mentors if m["email"] == "mentor2@example.com"]
    if not mentor_id:
        pytest.skip("멘토2 없음")
    mentor_id = mentor_id[0]
    # 매칭 요청 생성
    req = {
        "mentorId": mentor_id,
        "menteeId": 1,
        "message": "멘토링 요청합니다"
    }
    r = client.post("/api/match-requests", json=req, headers=mentee_headers)
    assert r.status_code == 200
    match_id = r.json()["id"]
    # 멘토가 받은 요청 확인
    r = client.get("/api/match-requests/incoming", headers=mentor_headers)
    assert r.status_code == 200
    # 멘티가 보낸 요청 확인
    r = client.get("/api/match-requests/outgoing", headers=mentee_headers)
    assert r.status_code == 200
    # 멘토가 요청 수락
    r = client.put(f"/api/match-requests/{match_id}/accept", headers=mentor_headers)
    assert r.status_code == 200
    # 멘티가 요청 취소
    r = client.delete(f"/api/match-requests/{match_id}", headers=mentee_headers)
    assert r.status_code in (200, 400, 404)
