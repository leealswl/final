"""
FastAPI with v6_rag integration
✅ MVP1: 사용자 입력 폼 자동 생성
"""

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from typing import List
from pathlib import Path

from v11_generator.ai_generator import generate_proposal

# 설정 import
from config import get_settings
import os

# v6_rag_real 모듈 import (프로덕션 전용)
from v6_rag_real import create_batch_graph

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import json

# 설정 로드
settings = get_settings()

class ChatRequest(BaseModel):
    userMessage: str
    userIdx: int | None = None
    projectIdx: int | None = None

# FastAPI 앱 초기화
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용으로 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],  # OPTIONS, POST, GET 등 모두 허용
    allow_headers=["*"],  # 모든 헤더 허용
)


# 앱 시작 시 그래프 한 번만 생성
batch_app = create_batch_graph()

# ========================================
# API 엔드포인트
# ========================================
@app.post("/analyze")
async def analyze_documents(
    files: List[UploadFile] = File(...),
    folders: List[str] = Form(...),
    userid: str = Form(...),
    projectidx: int = Form(...)
):
    """
    ✅ MVP1: 공고 + 첨부서류 분석 및 사용자 입력 폼 자동 생성

    디버깅: 422 에러가 발생하면 받은 파라미터를 로그로 출력

    Backend에서 받는 데이터 구조:
    - files: 업로드된 파일 리스트 (UploadFile 객체, 실제 파일 바이너리 포함)
    - folders: 각 파일이 속한 폴더 ID 리스트 (files와 1:1 매칭)
    - userid: 사용자 ID
    - projectidx: 프로젝트 ID

    예시:
    files[0] = UploadFile("2024_사업공고.pdf")  → folders[0] = "1" (공고 폴더)
    files[1] = UploadFile("붙임1_신청서.hwp")   → folders[1] = "2" (첨부서류 폴더)
    files[2] = UploadFile("붙임2_양식.xlsx")    → folders[2] = "2" (첨부서류 폴더)

    Returns:
    - form_source: 'TEMPLATE' (첨부 양식) or 'TOC' (공고 목차)
    - user_form: 사용자 입력 폼 스키마
    - documents: 분석된 문서 정보
    """
    try:
        # ========================================
        # 1단계: Backend에서 받은 데이터 검증
        # ========================================
        if len(files) != len(folders):
            raise ValueError(f"파일 개수({len(files)})와 폴더 개수({len(folders)})가 일치하지 않습니다.")

        print(f"📥 수신 데이터: userid={userid}, projectidx={projectidx}")
        print(f"📁 파일 개수: {len(files)}개")

        # ========================================
        # 2단계: 파일 바이트 변환 (디스크 저장 없이 메모리에서 처리)
        # ========================================
        # Backend가 이미 파일을 저장했으므로, FastAPI는 저장하지 않고
        # 바이트 데이터만 추출하여 LangGraph로 전달
        #
        # Backend가 보낸 files[i]와 folders[i]는 1:1 매칭됨
        # 예시:
        #   files[0] = UploadFile("공고.pdf")      folders[0] = "1"
        #   files[1] = UploadFile("붙임1.hwp")     folders[1] = "2"
        #   files[2] = UploadFile("붙임2.xlsx")    folders[2] = "2"

        saved_files = []
        for i, file in enumerate(files):
            folder_id = int(folders[i])  # "1" → 1, "2" → 2

            # UploadFile → 바이트 데이터 변환 (디스크 저장 안함!)
            file_bytes = await file.read()

            saved_files.append({
                "bytes": file_bytes,         # 파일 바이너리 데이터
                "filename": file.filename,   # 원본 파일명
                "folder": folder_id          # 1=공고, 2=첨부서류
            })

            # 디버깅 로그
            folder_type = "공고" if folder_id == 1 else "첨부서류"
            file_size_kb = len(file_bytes) / 1024
            print(f"  [{i}] {file.filename} → 폴더 {folder_id} ({folder_type}) - {file_size_kb:.1f}KB")

        print(f"✅ 파일 변환 완료: {len(saved_files)}개")

        # ========================================
        # 3단계: AI 분석을 위한 State 생성
        # ========================================
        # saved_files 구조:
        # [
        #   {"bytes": b"PDF binary...", "filename": "공고.pdf", "folder": 1},
        #   {"bytes": b"HWP binary...", "filename": "붙임1.hwp", "folder": 2},
        #   {"bytes": b"XLSX binary...", "filename": "붙임2.xlsx", "folder": 2}
        # ]

        state = {
            "files": saved_files,
            "user_id": userid,
            "project_idx": projectidx,
            "documents": [],
            "all_chunks": [],
            "all_embeddings": None,
            "embedding_model": None,
            "chroma_client": None,
            "chroma_collection": None,
            "vector_db_path": "",
            "extracted_features": [],
            # "cross_references": [],  # 🔖 MVP2에서 재구현 예정 (현재 미사용)
            "attachment_templates": [],  # ✨ MVP1
            "csv_paths": None,
            "oracle_ids": None,
            "response_data": {},
            "status": "initialized",
            "errors": []
        }

        # ========================================
        # 4단계: LangGraph AI 분석 실행
        # ========================================
        # v6_rag의 batch_app이 saved_files를 분석하여:
        # 1. folder=1 파일들 → 공고 분석 (TOC 추출)
        # 2. folder=2 파일들 → 첨부서류 분석 (양식 추출)
        # 3. 사용자 입력 폼 자동 생성
        print(f"🚀 LangGraph 분석 시작: project_idx={projectidx}")
        result = await run_in_threadpool(batch_app.invoke, state)
        print(f"✅ LangGraph 분석 완료")

        # ========================================
        # 5단계 LLM 호출 → JSON Plan 생성 [분리함]
        # ========================================
       
        # ========================================
        # 6단계: 분석 결과 반환
        # ========================================
        return JSONResponse(
            status_code=200,
            content=result['response_data']
        )

    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "서버 내부 오류가 발생했습니다.",
                "detail": str(e)
            }
        )


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok", "message": "Alice Consultant API is running"}


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": settings.API_TITLE,
        "version": settings.API_VERSION,
        "mvp1": "사용자 입력 폼 자동 생성",
        "endpoints": {
            "POST /analyze": "공고 및 첨부서류 분석",
            "GET /health": "헬스 체크"
        }
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        print("📢 Chat 요청 수신:", request.userMessage)
        print("📢 OpenAI 호출 키:", os.getenv("OPENAI_API_KEY") is not None)

        # 분석 단계 없이 바로 LLM 호출
        response_data = await generate_proposal(
            request.userMessage,
            request.userIdx,
            request.projectIdx,
            os.getenv("OPENAI_API_KEY")
        )


        return response_data

    except Exception as e:
        return {"error": str(e)}
    

# ========================================
# 실행 (개발용)
# ========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )
