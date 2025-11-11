"""
설정 및 상수
"""

from pathlib import Path

# ========================================
# 경로 설정
# ========================================
BASE_DIR = Path(__file__).parent.parent
VECTOR_DB_DIR = BASE_DIR / "vector_db"
CSV_OUTPUT_DIR = BASE_DIR / "parsed_results" / "v6_rag"

# 디렉토리 생성
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
CSV_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ========================================
# 모델 설정
# ========================================
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OPENAI_MODEL = "gpt-4o-mini"

# ========================================
# Feature 정의 (정부 R&D 공고문 기준)
# ========================================
FEATURES = [
    # 기본 정보
    {
        "feature_type": "사업명",
        "feature_key": "project_name",
        "description": "연구개발사업명 및 과제명",
        "keywords": {
            "primary": ["사업명", "과제명", "연구개발사업"],
            "secondary": ["지원사업", "사업과제명", "연구과제명", "세부사업명"]
        },
        "parent": None
    },
    {
        "feature_type": "공고번호",
        "feature_key": "announcement_number",
        "description": "공고 고유번호",
        "keywords": {
            "primary": ["공고번호", "과제공고번호"],
            "secondary": ["공고 번호", "RFP번호", "공고No"]
        },
        "parent": None
    },
    {
        "feature_type": "공고기관",
        "feature_key": "announcing_agency",
        "description": "공고 주관기관 및 전문기관",
        "keywords": {
            "primary": ["공고기관", "주관기관", "전문기관"],
            "secondary": ["주관부처", "발주기관", "사업관리기관"]
        },
        "parent": None
    },

    # 일정
    {
        "feature_type": "공고일",
        "feature_key": "announcement_date",
        "description": "공고 게시일",
        "keywords": {
            "primary": ["공고일", "게시일"],
            "secondary": ["공고일자", "공고게시일"]
        },
        "parent": None
    },
    {
        "feature_type": "접수기간",
        "feature_key": "application_period",
        "description": "과제 신청 접수 기간",
        "keywords": {
            "primary": ["접수기간", "신청기간"],
            "secondary": ["제출기한", "마감일", "신청마감"],
            "related": ["접수일정", "접수시작", "접수마감", "신청마감일"]
        },
        "parent": None
    },
    {
        "feature_type": "사업기간",
        "feature_key": "project_period",
        "description": "사업 수행 전체 기간",
        "keywords": {
            "primary": ["사업기간", "총사업기간"],
            "secondary": ["전체사업기간"]
        },
        "parent": None
    },

    # 자격 및 요건
    {
        "feature_type": "지원대상",
        "feature_key": "target",
        "description": "지원 가능 대상 기관 및 기업",
        "keywords": {
            "primary": ["지원대상", "신청대상", "참여대상"],
            "secondary": ["수행주체", "신청자", "참여기관"]
        },
        "parent": None
    },
    {
        "feature_type": "참여자격",
        "feature_key": "eligibility",
        "description": "참여 자격 요건 및 조건",
        "keywords": {
            "primary": ["참여자격", "신청자격", "지원자격"],
            "secondary": ["자격요건", "신청요건", "참여요건", "자격조건"]
        },
        "parent": None
    },
    {
        "feature_type": "참여제한",
        "feature_key": "restrictions",
        "description": "참여 제한 사항 및 결격사유",
        "keywords": {
            "primary": ["참여제한", "제한사항"],
            "secondary": ["제외대상", "결격사유", "신청제한", "참여불가"]
        },
        "parent": None
    },

    # 지원 내용
    {
        "feature_type": "지원규모",
        "feature_key": "support_scale",
        "description": "총 지원 규모 및 예산",
        "keywords": {
            "primary": ["지원규모", "지원예산", "총사업비"],
            "secondary": ["정부출연금", "정부지원금", "지원금액", "예산규모"]
        },
        "parent": None
    },
    {
        "feature_type": "지원기간",
        "feature_key": "support_period",
        "description": "과제 수행 기간",
        "keywords": {
            "primary": ["지원기간", "수행기간", "연구기간"],
            "secondary": ["개발기간", "과제기간"]
        },
        "parent": None
    },
    {
        "feature_type": "지원내용",
        "feature_key": "support_details",
        "description": "구체적 지원 내용 및 범위",
        "keywords": {
            "primary": ["지원내용", "지원범위"],
            "secondary": ["지원항목", "지원조건", "지원사항"]
        },
        "parent": None
    },

    # 제출 서류 (부모-자식 관계)
    {
        "feature_type": "제출서류",
        "feature_key": "submission_docs",
        "description": "제출 필요 서류 목록",
        "keywords": {
            "primary": ["제출서류", "제출자료", "구비서류"],
            "secondary": ["첨부서류", "제출물", "제출목록", "필수서류", "제출양식"]
        },
        "parent": None,
        "children": ["사업계획서", "사업계획서목차"]  # 하위 항목
    },
    {
        "feature_type": "사업계획서",
        "feature_key": "proposal",
        "description": "사업계획서 작성 요령 및 양식",
        "keywords": {
            "primary": ["사업계획서", "연구계획서", "제안서"],
            "secondary": ["계획서작성", "계획서양식", "RFP", "제안요청서"]
        },
        "parent": "제출서류",  # 상위 항목
        "children": ["사업계획서목차"]
    },
    {
        "feature_type": "사업계획서목차",
        "feature_key": "proposal_toc",
        "description": "사업계획서 작성 목차 구조",
        "keywords": {
            "primary": ["계획서목차", "작성목차"],
            "secondary": ["계획서구성", "작성항목", "기재사항"]
        },
        "parent": "사업계획서"  # 상위 항목
    },

    # 선정 및 평가 (부모-자식 관계)
    {
        "feature_type": "선정절차",
        "feature_key": "selection_process",
        "description": "과제 선정 절차 및 일정",
        "keywords": {
            "primary": ["선정절차", "선정과정"],
            "secondary": ["심사절차", "평가절차", "선정일정", "심사일정"]
        },
        "parent": None,
        "children": ["평가기준", "평가방법"]
    },
    {
        "feature_type": "평가기준",
        "feature_key": "evaluation_criteria",
        "description": "평가 기준 및 배점",
        "keywords": {
            "primary": ["평가기준", "심사기준", "선정기준"],
            "secondary": ["평가항목", "배점", "심사항목", "평가지표"]
        },
        "parent": "선정절차"
    },
    {
        "feature_type": "평가방법",
        "feature_key": "evaluation_method",
        "description": "평가 방식 및 방법",
        "keywords": {
            "primary": ["평가방법", "심사방법"],
            "secondary": ["평가방식", "심사방식", "평가절차"]
        },
        "parent": "선정절차"
    },

    # 법령 및 규정
    {
        "feature_type": "관련법령",
        "feature_key": "related_laws",
        "description": "관련 법령 및 규정",
        "keywords": {
            "primary": ["관련법령", "관련규정", "근거법령"],
            "secondary": ["법적근거", "시행령", "시행규칙", "훈령", "고시", "지침"]
        },
        "parent": None
    },
    {
        "feature_type": "관련제도",
        "feature_key": "related_systems",
        "description": "관련 제도 및 정책",
        "keywords": {
            "primary": ["관련제도", "관련정책"],
            "secondary": ["정부정책", "지원제도", "육성정책"]
        },
        "parent": None
    },

    # 기타
    {
        "feature_type": "사업목적",
        "feature_key": "project_objective",
        "description": "사업의 목적 및 필요성",
        "keywords": {
            "primary": ["사업목적", "추진목적"],
            "secondary": ["사업취지", "필요성", "추진배경"]
        },
        "parent": None
    },
    {
        "feature_type": "유의사항",
        "feature_key": "notice",
        "description": "신청 시 유의사항 및 주의사항",
        "keywords": {
            "primary": ["유의사항", "주의사항"],
            "secondary": ["안내사항", "참고사항", "준수사항", "확인사항"]
        },
        "parent": None
    },
    {
        "feature_type": "문의처",
        "feature_key": "contact",
        "description": "문의 담당자 및 연락처",
        "keywords": {
            "primary": ["문의처", "담당자", "연락처"],
            "secondary": ["문의전화", "담당부서", "문의사항"]
        },
        "parent": None
    },

    # 신청 방법
    {
        "feature_type": "신청방법",
        "feature_key": "application_method",
        "description": "신청 방법 및 절차",
        "keywords": {
            "primary": ["신청방법", "제출방법", "접수방법"],
            "secondary": ["온라인신청", "우편접수", "방문접수", "신청절차"]
        },
        "parent": None
    },
    {
        "feature_type": "신청서접수처",
        "feature_key": "submission_office",
        "description": "신청서 접수 장소 및 주소",
        "keywords": {
            "primary": ["접수처", "제출처", "신청서접수"],
            "secondary": ["접수주소", "제출주소", "방문접수처"]
        },
        "parent": None
    },

    # 예산 상세
    {
        "feature_type": "자부담비율",
        "feature_key": "self_burden_ratio",
        "description": "자부담 비율 및 조건",
        "keywords": {
            "primary": ["자부담", "자부담비율", "매칭비율"],
            "secondary": ["민간부담", "기업부담", "자체부담"]
        },
        "parent": "지원규모"
    },
    {
        "feature_type": "간접비",
        "feature_key": "indirect_cost",
        "description": "간접비 산정 기준",
        "keywords": {
            "primary": ["간접비", "간접경비"],
            "secondary": ["간접비율", "간접비산정"]
        },
        "parent": "지원규모"
    },
    {
        "feature_type": "사업비사용",
        "feature_key": "budget_usage",
        "description": "사업비 사용 범위 및 기준",
        "keywords": {
            "primary": ["사업비사용", "비목", "사용가능"],
            "secondary": ["집행기준", "사용범위", "집행내역"]
        },
        "parent": "지원규모"
    },

    # 연구 내용
    {
        "feature_type": "연구개발목표",
        "feature_key": "rd_objective",
        "description": "연구개발 목표 및 범위",
        "keywords": {
            "primary": ["연구목표", "개발목표", "과제목표"],
            "secondary": ["연구개발목표", "목표기술", "달성목표"]
        },
        "parent": None
    },
    {
        "feature_type": "연구개발내용",
        "feature_key": "rd_content",
        "description": "연구개발 세부 내용",
        "keywords": {
            "primary": ["연구내용", "개발내용", "연구범위"],
            "secondary": ["연구개발내용", "수행내용", "개발범위"]
        },
        "parent": None
    },
    {
        "feature_type": "기대효과",
        "feature_key": "expected_effect",
        "description": "기대효과 및 파급효과",
        "keywords": {
            "primary": ["기대효과", "예상효과"],
            "secondary": ["파급효과", "활용효과", "경제적효과"]
        },
        "parent": None
    },
    {
        "feature_type": "활용방안",
        "feature_key": "utilization_plan",
        "description": "연구 성과 활용 방안",
        "keywords": {
            "primary": ["활용방안", "사업화방안"],
            "secondary": ["성과활용", "실용화방안", "적용분야"]
        },
        "parent": None
    },

    # 협약 및 관리
    {
        "feature_type": "협약체결",
        "feature_key": "agreement",
        "description": "협약 체결 절차 및 내용",
        "keywords": {
            "primary": ["협약체결", "협약", "협약절차"],
            "secondary": ["협약서", "협약내용", "협약사항"]
        },
        "parent": None
    },
    {
        "feature_type": "사업관리",
        "feature_key": "project_management",
        "description": "사업 관리 및 점검",
        "keywords": {
            "primary": ["사업관리", "과제관리", "진도관리"],
            "secondary": ["현장점검", "관리점검", "이행점검"]
        },
        "parent": None
    },
    {
        "feature_type": "중간평가",
        "feature_key": "interim_evaluation",
        "description": "중간 평가 기준 및 시기",
        "keywords": {
            "primary": ["중간평가", "단계평가"],
            "secondary": ["중간점검", "진도평가"]
        },
        "parent": None
    },
    {
        "feature_type": "최종평가",
        "feature_key": "final_evaluation",
        "description": "최종 평가 기준",
        "keywords": {
            "primary": ["최종평가", "종료평가"],
            "secondary": ["결과평가", "성과평가"]
        },
        "parent": None
    },
    {
        "feature_type": "성과관리",
        "feature_key": "performance_management",
        "description": "성과 관리 및 보고",
        "keywords": {
            "primary": ["성과관리", "성과보고"],
            "secondary": ["성과지표", "성과목표", "성과제출"]
        },
        "parent": None
    },

    # 지식재산권
    {
        "feature_type": "지식재산권",
        "feature_key": "intellectual_property",
        "description": "지식재산권 귀속 및 관리",
        "keywords": {
            "primary": ["지식재산권", "특허", "지재권"],
            "secondary": ["지식재산권귀속", "특허출원", "기술이전"]
        },
        "parent": None
    },

    # 제재 및 제한
    {
        "feature_type": "중복지원제한",
        "feature_key": "duplicate_restriction",
        "description": "중복 지원 제한 사항",
        "keywords": {
            "primary": ["중복지원", "중복제한", "중복신청"],
            "secondary": ["중복불가", "중복참여제한"]
        },
        "parent": None
    },
    {
        "feature_type": "제재사항",
        "feature_key": "sanctions",
        "description": "제재 및 환수 조치",
        "keywords": {
            "primary": ["제재", "제재조치", "환수"],
            "secondary": ["환수조치", "허위신청", "부정수급", "사업비반환"]
        },
        "parent": None
    },
    {
        "feature_type": "정산",
        "feature_key": "settlement",
        "description": "사업비 정산 절차",
        "keywords": {
            "primary": ["정산", "사업비정산", "정산절차"],
            "secondary": ["정산보고", "비용정산", "집행정산"]
        },
        "parent": None
    },
]

# ========================================
# 청킹 설정
# ========================================
CHUNK_SETTINGS = {
    "min_length": 100,      # 최소 청크 길이
    "max_length": 1000,     # 최대 청크 길이
    "overlap": 50,          # 청크 간 오버랩
}

# ========================================
# RAG 설정
# ========================================
RAG_SETTINGS = {
    "top_k": 5,             # 검색할 최대 청크 수
    "score_threshold": 0.3, # 유사도 임계값
}
