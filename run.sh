#!/bin/bash
# 백엔드(FastAPI)와 프론트엔드(Vue) 개발 서버를 동시에 실행

# Python 패키지 설치
cd backend
pip install -r requirements.txt
cd ..

# 백엔드 실행 (8080)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8080 --reload &
BACK_PID=$!
cd ..

# 프론트엔드 실행 (3000)
cd frontend
npm install
npm run dev &
FRONT_PID=$!
cd ..

# 종료시 백/프론트 모두 종료
trap "kill $BACK_PID $FRONT_PID" EXIT
wait $BACK_PID $FRONT_PID
