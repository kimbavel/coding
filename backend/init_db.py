# Mentor-Mentee DB Schema (최소한의 구조)
import sqlite3

conn = sqlite3.connect('app.db')
c = conn.cursor()

# 사용자 테이블
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('mentor', 'mentee'))
)
''')

# 멘토 프로필
c.execute('''
CREATE TABLE IF NOT EXISTS mentor_profiles (
    user_id INTEGER PRIMARY KEY,
    bio TEXT,
    image_url TEXT,
    skills TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# 멘티 프로필
c.execute('''
CREATE TABLE IF NOT EXISTS mentee_profiles (
    user_id INTEGER PRIMARY KEY,
    bio TEXT,
    image_url TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# 매칭 요청
c.execute('''
CREATE TABLE IF NOT EXISTS match_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER NOT NULL,
    mentee_id INTEGER NOT NULL,
    message TEXT,
    status TEXT NOT NULL CHECK(status IN ('pending', 'accepted', 'rejected', 'cancelled')),
    FOREIGN KEY(mentor_id) REFERENCES users(id),
    FOREIGN KEY(mentee_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()
print('DB schema created.')
