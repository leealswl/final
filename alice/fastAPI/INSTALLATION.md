# FastAPI v6 설치 가이드

## 📦 필수 라이브러리 설치

### 1. Python 패키지 설치

```bash
cd alice/fastAPI
pip install -r requirements.txt
```

### 2. 시스템 라이브러리 설치 (pdf2image 사용 시 필수)

`pdf2image`는 PDF를 이미지로 변환하기 위해 **poppler** 시스템 라이브러리가 필요합니다.

#### macOS
```bash
brew install poppler
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

#### Windows
⚠️ **중요**: poppler는 시스템 라이브러리이므로 `requirements.txt`에 포함할 수 없습니다. 수동 설치가 필요합니다.

**자동 설치 (권장)**:

1. **PowerShell 열기** (시작 메뉴에서 "PowerShell" 검색)
   - ⚠️ **관리자 권한으로 실행** 권장 (우클릭 → "관리자 권한으로 실행")

2. **실행 정책 변경** (최초 1회만):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
   - 보안 경고가 나오면 `Y` 입력

3. **스크립트 실행**:
   ```powershell
   cd alice\fastAPI
   .\install_poppler_windows.ps1
   ```
   
   또는 절대 경로로:
   ```powershell
   .\alice\fastAPI\install_poppler_windows.ps1
   ```

**참고**: 
- 실행 정책 변경 없이 실행하려면: `powershell -ExecutionPolicy Bypass -File .\install_poppler_windows.ps1`
- 스크립트는 poppler를 자동으로 다운로드하고 PATH에 추가합니다

**수동 설치**:
1. https://github.com/oschwartz10612/poppler-windows/releases 에서 최신 버전 다운로드
2. 압축 해제 후 `bin` 폴더 경로를 시스템 PATH 환경 변수에 추가
3. PowerShell 재시작
4. 설치 확인: `pdftoppm.exe -v`

### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
STORAGE_MODE=csv  # 또는 oracle
```

## 🔍 오늘 추가된 주요 라이브러리

### Vision API 관련
- **pdf2image==1.17.0**: PDF를 이미지로 변환 (Vision API 분석용)
- **pillow==11.0.0**: 이미지 처리 (pdf2image 의존성)
- **openai==1.58.1**: OpenAI API 클라이언트 (GPT-4o Vision 사용)

### 기존 라이브러리
- **fastapi==0.115.6**: FastAPI 프레임워크
- **uvicorn==0.34.0**: ASGI 서버
- **chromadb==1.3.3**: 벡터 데이터베이스
- **langchain==0.3.13**: LLM 프레임워크
- **langgraph==0.2.60**: LangGraph (워크플로우 관리)
- **pandas==2.2.3**: 데이터 처리
- **numpy==1.26.4**: 수치 계산
- **pdfplumber==0.10.3**: PDF 텍스트 추출

## ⚠️ 주의사항

1. **poppler 설치 확인**: 
   ```bash
   pdftoppm -v  # poppler 설치 확인
   ```

2. **Vision API 사용 시**: 
   - OpenAI API 키가 필요합니다
   - GPT-4o 모델에 접근 권한이 있어야 합니다

3. **메모리 요구사항**:
   - PDF를 이미지로 변환 시 메모리를 많이 사용할 수 있습니다
   - 큰 PDF 파일의 경우 배치 처리를 권장합니다

## 🐛 문제 해결

### pdf2image 오류
```
pdf2image.exceptions.PDFInfoNotInstalledError
```
→ poppler가 설치되지 않았거나 PATH에 없는 경우입니다. 위의 시스템 라이브러리 설치 단계를 확인하세요.

### 메모리 부족 오류
→ PDF 파일 크기를 줄이거나, 배치 크기를 줄여서 처리하세요.

## 📚 참고 자료

- [pdf2image 공식 문서](https://github.com/Belval/pdf2image)
- [poppler 공식 사이트](https://poppler.freedesktop.org/)
- [OpenAI Vision API 문서](https://platform.openai.com/docs/guides/vision)

