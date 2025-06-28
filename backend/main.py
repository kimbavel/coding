from fastapi import FastAPI, HTTPException, Depends, Request, status, Body
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sqlite3
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
import jwt
import os
import importlib.util

app = FastAPI(openapi_url="/api/openapi.json", docs_url="/api/docs")

# CORS 설정 (프론트엔드와 통신 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# DB 연결 함수
DB_PATH = "./backend/app.db"

def init_db():
    # init_db.py를 import해서 실행
    import importlib.util
    import os
    db_init_path = os.path.join(os.path.dirname(__file__), "init_db.py")
    spec = importlib.util.spec_from_file_location("init_db", db_init_path)
    db_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_module)

init_db()  # 앱 시작 시 DB 초기화

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 에러 핸들러
@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)}
    )

# JWT 기반 인증 의존성
SECRET_KEY = "dev-secret"  # 실제 서비스에서는 환경변수 사용

def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return payload

# 기본 라우트 예시
@app.get("/api/health")
def health():
    return {"status": "ok"}

# 회원가입 관련 모델
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str  # mentor or mentee

# 회원가입
@app.post("/api/signup", status_code=201)
def signup(data: SignupRequest = Body(...)):
    conn = get_db()
    c = conn.cursor()
    try:
        hashed_pw = bcrypt.hash(data.password)
        c.execute(
            "INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
            (data.email, hashed_pw, data.name, data.role)
        )
        user_id = c.lastrowid
        if data.role == "mentor":
            c.execute("INSERT INTO mentor_profiles (user_id, bio, image_url, skills) VALUES (?, '', '', '')", (user_id,))
        else:
            c.execute("INSERT INTO mentee_profiles (user_id, bio, image_url) VALUES (?, '', '')", (user_id,))
        conn.commit()
        return {"message": "User created"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already exists")
    finally:
        conn.close()

# 로그인
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/api/login")
def login(data: LoginRequest = Body(...)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, password, role FROM users WHERE email = ?", (data.email,))
    user = c.fetchone()
    conn.close()
    if not user or not bcrypt.verify(data.password, user[1]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode({"user_id": user[0], "role": user[2]}, SECRET_KEY, algorithm="HS256")
    return {"token": token}

# 내 정보 조회
@app.get("/api/me")
def get_me(user=Depends(get_current_user)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, email, name, role FROM users WHERE id = ?", (user["user_id"],))
    u = c.fetchone()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    # 프로필 정보
    if u[3] == "mentor":
        c.execute("SELECT bio, image_url, skills FROM mentor_profiles WHERE user_id = ?", (u[0],))
        p = c.fetchone()
        profile = {
            "name": u[2],
            "bio": p[0] if p else "",
            "imageUrl": p[1] if p else "",
            "skills": (p[2].split(",") if p and p[2] else [])
        }
        return {"id": u[0], "email": u[1], "role": u[3], "profile": profile}
    else:
        c.execute("SELECT bio, image_url FROM mentee_profiles WHERE user_id = ?", (u[0],))
        p = c.fetchone()
        profile = {
            "name": u[2],
            "bio": p[0] if p else "",
            "imageUrl": p[1] if p else ""
        }
        return {"id": u[0], "email": u[1], "role": u[3], "profile": profile}

# 프로필 수정 (멘토/멘티)
class UpdateMentorProfileRequest(BaseModel):
    id: int
    name: str
    role: str
    bio: str
    image: str  # base64
    skills: list[str]

class UpdateMenteeProfileRequest(BaseModel):
    id: int
    name: str
    role: str
    bio: str
    image: str  # base64

from fastapi import UploadFile
import base64

@app.put("/api/profile")
def update_profile(
    user=Depends(get_current_user),
    mentor_data: UpdateMentorProfileRequest = None,
    mentee_data: UpdateMenteeProfileRequest = None
):
    conn = get_db()
    c = conn.cursor()
    if user["role"] == "mentor" and mentor_data:
        # 이미지 저장 (여기선 base64를 파일로 저장하지 않고, image_url만 저장)
        c.execute("UPDATE users SET name=? WHERE id=?", (mentor_data.name, user["user_id"]))
        c.execute(
            "UPDATE mentor_profiles SET bio=?, image_url=?, skills=? WHERE user_id=?",
            (mentor_data.bio, "", ",".join(mentor_data.skills), user["user_id"])
        )
        conn.commit()
        return {"result": "ok"}
    elif user["role"] == "mentee" and mentee_data:
        c.execute("UPDATE users SET name=? WHERE id=?", (mentee_data.name, user["user_id"]))
        c.execute(
            "UPDATE mentee_profiles SET bio=?, image_url=? WHERE user_id=?",
            (mentee_data.bio, "", user["user_id"])
        )
        conn.commit()
        return {"result": "ok"}
    else:
        raise HTTPException(status_code=400, detail="Invalid request")

# 멘토 목록 조회
from typing import Optional

@app.get("/api/mentors")
def get_mentors(skill: Optional[str] = None, orderBy: Optional[str] = None, user=Depends(get_current_user)):
    if user["role"] != "mentee":
        raise HTTPException(status_code=401, detail="Only mentee can access mentor list")
    conn = get_db()
    c = conn.cursor()
    query = "SELECT u.id, u.email, u.role, u.name, p.bio, p.image_url, p.skills FROM users u JOIN mentor_profiles p ON u.id = p.user_id WHERE u.role = 'mentor'"
    params = []
    if skill:
        query += " AND p.skills LIKE ?"
        params.append(f"%{skill}%")
    if orderBy == "skill":
        query += " ORDER BY p.skills ASC"
    elif orderBy == "name":
        query += " ORDER BY u.name ASC"
    c.execute(query, params)
    mentors = [
        {
            "id": row[0],
            "email": row[1],
            "role": row[2],
            "profile": {
                "name": row[3],
                "bio": row[4],
                "imageUrl": row[5],
                "skills": row[6].split(",") if row[6] else []
            }
        }
        for row in c.fetchall()
    ]
    return mentors

# 매칭 요청 관련 모델
class MatchRequestCreate(BaseModel):
    mentorId: int
    menteeId: int
    message: str

class MatchRequest(BaseModel):
    id: int
    mentorId: int
    menteeId: int
    message: str
    status: str

# 매칭 요청 생성
@app.post("/api/match-requests")
def create_match_request(data: MatchRequestCreate, user=Depends(get_current_user)):
    if user["role"] != "mentee" or user["user_id"] != data.menteeId:
        raise HTTPException(status_code=401, detail="Only mentee can send match request for self")
    conn = get_db()
    c = conn.cursor()
    # 멘토 존재 확인
    c.execute("SELECT id FROM users WHERE id=? AND role='mentor'", (data.mentorId,))
    if not c.fetchone():
        raise HTTPException(status_code=400, detail="Mentor not found")
    c.execute(
        "INSERT INTO match_requests (mentor_id, mentee_id, message, status) VALUES (?, ?, ?, 'pending')",
        (data.mentorId, data.menteeId, data.message)
    )
    conn.commit()
    req_id = c.lastrowid
    conn.close()
    return {"id": req_id, "mentorId": data.mentorId, "menteeId": data.menteeId, "message": data.message, "status": "pending"}

# 멘토: 받은 매칭 요청 조회
@app.get("/api/match-requests/incoming")
def get_incoming_match_requests(user=Depends(get_current_user)):
    if user["role"] != "mentor":
        raise HTTPException(status_code=401, detail="Only mentor can view incoming requests")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, mentor_id, mentee_id, message, status FROM match_requests WHERE mentor_id=?", (user["user_id"],))
    result = [
        {"id": row[0], "mentorId": row[1], "menteeId": row[2], "message": row[3], "status": row[4]}
        for row in c.fetchall()
    ]
    conn.close()
    return result

# 멘티: 보낸 매칭 요청 조회
@app.get("/api/match-requests/outgoing")
def get_outgoing_match_requests(user=Depends(get_current_user)):
    if user["role"] != "mentee":
        raise HTTPException(status_code=401, detail="Only mentee can view outgoing requests")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, mentor_id, mentee_id, status FROM match_requests WHERE mentee_id=?", (user["user_id"],))
    result = [
        {"id": row[0], "mentorId": row[1], "menteeId": row[2], "status": row[3]}
        for row in c.fetchall()
    ]
    conn.close()
    return result

# 매칭 요청 수락/거절/취소
@app.put("/api/match-requests/{id}/accept")
def accept_match_request(id: int, user=Depends(get_current_user)):
    if user["role"] != "mentor":
        raise HTTPException(status_code=401, detail="Only mentor can accept requests")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT mentor_id, status FROM match_requests WHERE id=?", (id,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Match request not found")
    if row[0] != user["user_id"]:
        raise HTTPException(status_code=401, detail="Not your request")
    c.execute("UPDATE match_requests SET status='accepted' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"result": "accepted"}

@app.put("/api/match-requests/{id}/reject")
def reject_match_request(id: int, user=Depends(get_current_user)):
    if user["role"] != "mentor":
        raise HTTPException(status_code=401, detail="Only mentor can reject requests")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT mentor_id, status FROM match_requests WHERE id=?", (id,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Match request not found")
    if row[0] != user["user_id"]:
        raise HTTPException(status_code=401, detail="Not your request")
    c.execute("UPDATE match_requests SET status='rejected' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"result": "rejected"}

@app.delete("/api/match-requests/{id}")
def cancel_match_request(id: int, user=Depends(get_current_user)):
    if user["role"] != "mentee":
        raise HTTPException(status_code=401, detail="Only mentee can cancel requests")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT mentee_id, status FROM match_requests WHERE id=?", (id,))
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Match request not found")
    if row[0] != user["user_id"]:
        raise HTTPException(status_code=401, detail="Not your request")
    c.execute("UPDATE match_requests SET status='cancelled' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"result": "cancelled"}

# 프로필 이미지 조회
@app.get("/api/images/{role}/{id}")
def get_profile_image(role: str, id: int, user=Depends(get_current_user)):
    # 실제로는 파일 경로를 DB에 저장하거나, 기본 이미지를 제공
    # 여기서는 예시로 static 폴더에서 role/id.jpg 또는 id.png를 찾음
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    for ext in ["jpg", "png"]:
        img_path = os.path.join(static_dir, f"{role}_{id}.{ext}")
        if os.path.exists(img_path):
            return FileResponse(img_path, media_type=f"image/{ext}")
    # 없으면 404
    raise HTTPException(status_code=404, detail="Image not found")

# TODO: openapi.yaml 기반 엔드포인트 구현

@app.get("/")
def root():
    return RedirectResponse(url="/api/docs")
