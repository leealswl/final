# 📋 라이브러리 설치 요약

## 🆕 오늘 추가된 라이브러리 (2025-11-29)

### Vision API 관련
다음 라이브러리들은 Vision API를 통한 PDF 이미지 분석 기능을 위해 추가되었습니다.

| 라이브러리 | 버전 | 용도 | 설치 방법 |
|---------|------|------|----------|
| `pdf2image` | 1.17.0 | PDF를 이미지로 변환 (Vision API 분석용) | `pip install pdf2image==1.17.0` |
| `pillow` | 11.0.0 | 이미지 처리 (pdf2image 의존성) | `pip install pillow==11.0.0` |
| `openai` | 1.58.1 | OpenAI API 클라이언트 (GPT-4o Vision) | `pip install openai==1.58.1` |

### 시스템 라이브러리 (pip로 설치 불가)
| 라이브러리 | OS별 설치 방법 |
|---------|-------------|
| `poppler` | **macOS**: `brew install poppler`<br>**Ubuntu/Debian**: `sudo apt-get install poppler-utils`<br>**Windows**: [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases) 다운로드 |

## 📦 전체 설치 방법

### 1. Python 패키지 설치
```bash
cd alice/fastAPI
pip install -r requirements.txt
```

### 2. 시스템 라이브러리 설치 (필수)
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install poppler-utils

# Windows
# 위의 링크에서 다운로드 후 PATH 설정
```

### 3. 설치 확인
```bash
# poppler 확인
pdftoppm -v

# Python 패키지 확인
python -c "import pdf2image; print('pdf2image OK')"
python -c "import openai; print('openai OK')"
```

## 🔍 사용 위치

### pdf2image
- `src/v6_rag_real/nodes/metadata_vision.py`: 공고문 메타 정보 추출
- `src/v6_rag_real/nodes/toc_util.py`: 목차 추출 (Vision API)

### openai
- `src/v6_rag_real/nodes/metadata_vision.py`: GPT-4o Vision API 호출
- `src/v6_rag_real/nodes/toc_util.py`: GPT-4o Vision API 호출
- `src/v6_rag_real/nodes/processing.py`: OpenAI Embedding API, GPT-4o-mini

## 📝 requirements.txt 업데이트 내역

### 추가된 항목
```txt
# AI/ML 라이브러리
openai==1.58.1  # 추가됨

# PDF 처리
pdf2image==1.17.0  # 추가됨 (Vision API용)

# 이미지 처리
pillow==11.0.0  # 추가됨 (pdf2image 의존성)
```

## ⚠️ 주의사항

1. **poppler 필수**: pdf2image를 사용하려면 반드시 poppler 시스템 라이브러리가 설치되어 있어야 합니다.

2. **OpenAI API 키**: `.env` 파일에 `OPENAI_API_KEY`를 설정해야 Vision API를 사용할 수 있습니다.

3. **메모리 사용량**: 큰 PDF 파일을 이미지로 변환할 때 메모리를 많이 사용할 수 있습니다.

## 🔗 참고 링크

- [INSTALLATION.md](./INSTALLATION.md): 상세 설치 가이드
- [requirements.txt](./requirements.txt): 전체 라이브러리 목록

