"""
FastAPI with v6_rag integration
✅ MVP1: 사용자 입력 폼 자동 생성
"""

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
<<<<<<< HEAD
from typing import List, Optional
=======
from typing import List
>>>>>>> dev
from pathlib import Path

# 설정 import
from config import get_settings
import os

<<<<<<< HEAD
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

=======
>>>>>>> dev
# v6_rag_real 모듈 import (프로덕션 전용)
from v6_rag_real import create_batch_graph

# 설정 로드
settings = get_settings()

# FastAPI 앱 초기화
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION
)

<<<<<<< HEAD
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 앱 시작 시 그래프 한 번만 생성
batch_app = create_batch_graph()


class ProposalRequest(BaseModel):
    project_title: Optional[str] = None
    goal: Optional[str] = None
    requirements: Optional[List[str]] = None
    deliverables: Optional[List[str]] = None
    tone: Optional[str] = None
    extra: Optional[str] = None


class PolishRequest(BaseModel):
    text: str


def _render_list(items: Optional[List[str]]) -> str:
    if not items:
        return "<p>• (내용 없음)</p>"
    lines = []
    lines.append("<ul>")
    for item in items:
        if not item:
            continue
        lines.append(f"  <li>{item}</li>")
    lines.append("</ul>")
    return "\n".join(lines)


def _render_section(title: str, body: str) -> str:
    return f"<h2>{title}</h2>\n{body}"

=======
# 앱 시작 시 그래프 한 번만 생성
batch_app = create_batch_graph()

>>>>>>> dev
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

<<<<<<< HEAD
=======
    디버깅: 422 에러가 발생하면 받은 파라미터를 로그로 출력

>>>>>>> dev
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

<<<<<<< HEAD
        # ✨ 저장 모드 결정: 환경변수 기반
        storage_mode = os.getenv('STORAGE_MODE', 'csv')  # 기본값: csv (개발)
        oracle_config = None

        # 프로덕션 환경: Oracle DB 설정
        if storage_mode == 'oracle':
            oracle_config = {
                'user': os.getenv('ORACLE_USER'),
                'password': os.getenv('ORACLE_PASSWORD'),
                'dsn': os.getenv('ORACLE_DSN')  # 예: localhost:1521/ORCL
            }
            print(f"🔵 Oracle 저장 모드 활성화: {oracle_config['dsn']}")
        else:
            print(f"🟢 CSV 저장 모드 (개발)")

=======
>>>>>>> dev
        state = {
            "files": saved_files,
            "user_id": userid,
            "project_idx": projectidx,
<<<<<<< HEAD
            "storage_mode": storage_mode,          # ✨ 'csv' or 'oracle'
            "oracle_config": oracle_config,        # ✨ Oracle 설정 (프로덕션)
=======
>>>>>>> dev
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
        # 5단계: 분석 결과 반환
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


<<<<<<< HEAD
def polish_to_formal(text: str) -> str:
    base = text.strip()
    if not base:
        return ""
    sentence = base[0].upper() + base[1:]
    if not sentence.endswith("니다."):
        sentence = sentence.rstrip(". ") + "입니다."
    return sentence


@app.post("/polish-text")
async def polish_text(request: PolishRequest):
    if not request.text or not request.text.strip():
        return JSONResponse(status_code=400, content={"status": "fail", "message": "다듬을 문장을 입력해 주세요."})

    refined = polish_to_formal(request.text)
    return JSONResponse(status_code=200, content={"status": "success", "refined": refined})


@app.post("/generate-proposal")
async def generate_proposal(request: ProposalRequest):
    """AI 제안서 초안 생성 (샘플 템플릿 기반)"""

    project_title = request.project_title or "제안 프로젝트"
    goal = request.goal or "프로젝트 목표가 입력되지 않았습니다."
    tone = request.tone or "공문체"
    requirements_html = _render_list(request.requirements)
    deliverables_html = _render_list(request.deliverables)
    extra_html = (
        f"<p><strong>추가 요청</strong>: {request.extra}</p>"
        if request.extra else ""
    )

    effects_html = _render_list([
        "행정 문서 작성 시간 단축",
        "공문체 품질 향상 및 오류 감소",
        "협업 프로세스 자동화로 대응력 강화",
    ])

    sections = [
        _render_section("1. 제안 개요", f"<p>{goal}</p>"),
        _render_section("2. 추진 목표 및 필요성", (
            "<p>본 과제는 행정 효율화를 위해 AI 기반 시스템을 구축하여 "
            "사업 추진 속도와 품질을 동시에 개선하고자 합니다.</p>"
            "<p>주요 기대 효과는 다음과 같습니다:</p>"
            f"{effects_html}"
        )),
        _render_section("3. 핵심 요구사항", requirements_html),
        _render_section("4. 주요 산출물", deliverables_html),
        _render_section("5. 추진 일정(예시)", (
            "<ul>"
            "<li>1단계 (1개월) : 요구사항 정밀 분석 및 데이터 수집</li>"
            "<li>2단계 (2개월) : AI 모델 설계 및 프로토타입 구현</li>"
            "<li>3단계 (2개월) : 사용자 피드백 기반 고도화 및 안정화</li>"
            "<li>4단계 (1개월) : 운영 전환 및 교육, 성과 측정</li>"
            "</ul>"
        )),
    ]

    article_html = "\n".join(sections)
    proposal_html = (
        f"<article>"
        f"<h1>{project_title}</h1>"
        f"<p><em>작성 톤: {tone}</em></p>"
        f"{article_html}"
        f"{extra_html}"
        f"</article>"
    )

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "proposal_html": proposal_html,
            "meta": {
                "project_title": project_title,
                "tone": tone,
            }
        }
    )


=======
>>>>>>> dev
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
