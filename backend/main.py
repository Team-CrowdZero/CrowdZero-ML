from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# ✅ CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (보안 설정 필요 시 변경 가능)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

# 데이터를 저장할 리스트
protests = []

# 데이터 구조 정의
class Protest(BaseModel):
    date: str
    location: str
    participants: int

@app.get("/get_protests")
def get_protests():
    return {"protests": protests}

@app.post("/add_protest")
def add_protests(data: dict):
    global protests
    protests = data["protests"]  # 크롤러에서 받은 데이터 저장
    return {"message": "시위 일정 업데이트 완료", "data": protests}

@app.get("/")
def root():
    return {"message": "FastAPI 서버가 정상적으로 실행 중입니다!"}
