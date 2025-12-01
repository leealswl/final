# Windows 설치 가이드

## PowerShell 스크립트 실행 방법

### 1. PowerShell 열기

1. **시작 메뉴**에서 "PowerShell" 검색
2. **Windows PowerShell** 또는 **PowerShell** 실행
3. ⚠️ **관리자 권한으로 실행** 권장 (우클릭 → "관리자 권한으로 실행")

### 2. 실행 정책 변경 (최초 1회만)

PowerShell에서 스크립트를 실행하려면 실행 정책을 변경해야 합니다:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

보안 경고가 나타나면:
- `Y` 또는 `A` 입력하여 예(Y)로 답변

**설명**:
- `RemoteSigned`: 로컬에서 만든 스크립트는 서명 없이 실행 가능
- `Scope CurrentUser`: 현재 사용자에게만 적용 (시스템 전체에 영향 없음)

### 3. 스크립트 실행

프로젝트 폴더로 이동 후 스크립트 실행:

```powershell
# 프로젝트 루트로 이동
cd C:\path\to\alice_consultant_agent_real\final

# 또는 직접 fastAPI 폴더로 이동
cd alice\fastAPI

# 스크립트 실행
.\install_poppler_windows.ps1
```

### 4. 실행 정책 변경 없이 실행 (대안)

실행 정책을 변경하고 싶지 않은 경우:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_poppler_windows.ps1
```

## Poppler 설치 후 확인

스크립트 실행 후 PowerShell을 **재시작**하고 다음 명령으로 확인:

```powershell
pdftoppm.exe -v
```

정상적으로 설치되었다면 버전 정보가 출력됩니다.

## 문제 해결

### "실행할 수 없는 스크립트" 오류

**증상**:
```
.\install_poppler_windows.ps1: 이 시스템에서 스크립트를 실행할 수 없으므로 ...
```

**해결**:
1. 실행 정책 변경 (위의 2번 단계 참고)
2. 또는 `-ExecutionPolicy Bypass` 옵션 사용

### "액세스가 거부되었습니다" 오류

**증상**:
```
액세스가 거부되었습니다
```

**해결**:
1. PowerShell을 **관리자 권한**으로 실행
2. 또는 사용자 환경 변수 대신 시스템 환경 변수에 수동 추가

### PATH에 추가되지 않음

**해결**:
1. PowerShell 재시작
2. 또는 수동으로 PATH 추가:
   - 환경 변수 편집 → 사용자 변수 → Path → 편집
   - `C:\Users\YourName\AppData\Local\poppler\poppler-*\Library\bin` 추가

## 수동 설치 방법

스크립트 실행이 어려운 경우:

1. **다운로드**:
   - https://github.com/oschwartz10612/poppler-windows/releases
   - 최신 `Release-*.zip` 파일 다운로드

2. **압축 해제**:
   - 원하는 위치에 압축 해제 (예: `C:\Program Files\poppler`)

3. **PATH 추가**:
   - 환경 변수 편집 → Path → 새로 만들기
   - `C:\Program Files\poppler\Library\bin` 추가 (실제 경로에 맞게 수정)

4. **확인**:
   - PowerShell 재시작
   - `pdftoppm.exe -v` 실행

## 추가 정보

- 스크립트는 poppler를 `%LOCALAPPDATA%\poppler`에 설치합니다
- PATH 환경 변수에 자동으로 추가합니다
- 설치 후 PowerShell 재시작이 필요할 수 있습니다

