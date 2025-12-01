# Windows용 Poppler 자동 설치 스크립트
# 
# 사용 방법:
#   PowerShell에서 관리자 권한으로 실행:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   .\install_poppler_windows.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Poppler for Windows 자동 설치" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$popplerUrl = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
$downloadPath = "$env:TEMP\poppler-windows.zip"
$installPath = "$env:LOCALAPPDATA\poppler"

# 1. 다운로드
Write-Host "[1/4] Poppler 다운로드 중..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $popplerUrl -OutFile $downloadPath -UseBasicParsing
    Write-Host "✓ 다운로드 완료" -ForegroundColor Green
} catch {
    Write-Host "✗ 다운로드 실패: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "수동 설치 방법:" -ForegroundColor Yellow
    Write-Host "  1. https://github.com/oschwartz10612/poppler-windows/releases 에서 최신 버전 다운로드"
    Write-Host "  2. 압축 해제 후 bin 폴더 경로를 PATH 환경 변수에 추가"
    exit 1
}

# 2. 압축 해제
Write-Host "[2/4] 압축 해제 중..." -ForegroundColor Yellow
try {
    if (Test-Path $installPath) {
        Remove-Item -Path $installPath -Recurse -Force
    }
    Expand-Archive -Path $downloadPath -DestinationPath $installPath -Force
    Write-Host "✓ 압축 해제 완료" -ForegroundColor Green
} catch {
    Write-Host "✗ 압축 해제 실패: $_" -ForegroundColor Red
    exit 1
}

# 3. PATH에 추가
Write-Host "[3/4] PATH 환경 변수에 추가 중..." -ForegroundColor Yellow
$popplerBinPath = Join-Path $installPath "poppler-*\Library\bin"
$popplerBinPath = (Resolve-Path $popplerBinPath).Path

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$popplerBinPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$popplerBinPath", "User")
    Write-Host "✓ PATH 추가 완료" -ForegroundColor Green
    Write-Host "  경로: $popplerBinPath" -ForegroundColor Gray
} else {
    Write-Host "✓ PATH에 이미 추가되어 있음" -ForegroundColor Green
}

# 4. 설치 확인
Write-Host "[4/4] 설치 확인 중..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

try {
    $version = & "$popplerBinPath\pdftoppm.exe" -v 2>&1
    Write-Host "✓ 설치 확인 완료" -ForegroundColor Green
    Write-Host "  버전: $version" -ForegroundColor Gray
} catch {
    Write-Host "⚠ 설치 확인 실패 (PowerShell 재시작 후 다시 시도)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "설치 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  중요: PATH 변경사항 적용을 위해 PowerShell을 재시작하세요." -ForegroundColor Yellow
Write-Host ""
Write-Host "설치 확인:" -ForegroundColor Cyan
Write-Host "  pdftoppm -v" -ForegroundColor Gray
Write-Host ""

# 정리
Remove-Item $downloadPath -ErrorAction SilentlyContinue

