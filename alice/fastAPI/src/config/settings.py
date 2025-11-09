"""
Application settings configuration
환경 변수 및 애플리케이션 설정을 관리합니다.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # API 메타데이터
    API_TITLE: str = "Alice Consultant API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "공고 분석 및 사용자 입력 폼 자동 생성 API"

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True  # 개발 모드에서만 True

    # 파일 업로드 설정
    UPLOAD_DIR: Path = Path("./uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # 스토리지 설정
    STORAGE_MODE: str = "csv"  # "csv" or "oracle"

    # Oracle 설정 (필요시)
    ORACLE_USER: Optional[str] = None
    ORACLE_PASSWORD: Optional[str] = None
    ORACLE_DSN: Optional[str] = None

    # RAG 설정
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 싱글톤 인스턴스
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    애플리케이션 설정 싱글톤을 반환합니다.

    Returns:
        Settings: 애플리케이션 설정 객체
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        # 업로드 디렉토리 생성
        _settings.UPLOAD_DIR.mkdir(exist_ok=True)
    return _settings
