"""
Vision API 기반 메타 정보 추출 유틸리티

✅ 핵심 기능: 공고문의 첫 10페이지를 Vision API로 직접 분석하여
             사업명, 공고번호, 공고일, 공고기관 등 핵심 메타 정보를 정확하게 추출

📌 특징:
  - 텍스트 추출의 한계 극복 (폰트 인코딩, 레이아웃 파싱 실패 등)
  - 제목/헤더 부분의 레이아웃 정보 활용
  - 정확도 향상을 위한 Vision API 전용 파이프라인
  - 첫 10페이지까지 분석하여 핵심 정보가 여러 페이지에 분산된 경우도 처리
"""

import io
import base64
import json
from typing import Dict, Optional, Any
from openai import OpenAI
import os
from dotenv import load_dotenv

# OpenAI 클라이언트 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_metadata_with_vision(
    file_bytes: bytes,
    file_name: str,
    feature_type: str,
    feature_description: str,
    feature_key: str = None  # Feature 키 (날짜 포함 여부 판단용)
) -> Optional[Dict[str, Any]]:
    """
    Vision API를 사용하여 공고문 첫 10페이지에서 메타 정보 추출
    
    Args:
        file_bytes: PDF 파일의 바이트 데이터
        file_name: 파일명 (로깅용)
        feature_type: 추출할 Feature 타입 (예: "사업명", "공고번호")
        feature_description: Feature 설명
    
    Returns:
        추출된 메타 정보 딕셔너리 또는 None
        {
            "found": true/false,
            "title": "추출된 실제 값",
            "content": "실제 값",
            "full_content": "전체 문맥",
            "key_points": [...],
            "writing_strategy": {...}
        }
    """
    try:
        from pdf2image import convert_from_bytes
    except ImportError:
        print(f"    ⚠️  pdf2image 라이브러리가 설치되지 않았습니다.")
        return None

    try:
        print(f"    👁️  Vision API로 {feature_type} 추출 중...")

        # 첫 10페이지까지 분석 (핵심 정보는 앞쪽 페이지에 분산될 수 있음)
        images = convert_from_bytes(
            file_bytes,
            dpi=150,  # 높은 해상도로 제목/헤더 부분 정확하게 인식
            first_page=1,
            last_page=10
        )

        if not images:
            print(f"    ⚠️  PDF 이미지 변환 실패")
            return None

        # 이미지를 base64로 인코딩
        image_contents = []
        for idx, img in enumerate(images):
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}",
                    "detail": "high"  # 높은 디테일로 제목/헤더 정확히 인식
                }
            })

        # 날짜/기간이 필요한 Feature인지 판단
        date_required_features = ['announcement_date', 'application_period', 'project_period']
        requires_date = feature_key in date_required_features if feature_key else False
        
        # 시스템 프롬프트: Feature 타입에 따라 조건부 작성
        if requires_date:
            # 날짜/기간 정보가 필요한 Feature (공고일, 접수기간, 사업기간)
            content_instruction = f"""실제 {feature_type} 값 - **구체적인 날짜/기간을 반드시 포함** (예: '2025년 9월 9일', '2025년 10월 1일 ~ 2026년 12월 31일')"""
            date_emphasis = """
**⚠️ 매우 중요 (날짜/기간 정보):**
- content 필드에는 **구체적인 날짜나 기간**을 반드시 포함하세요
- 요약하지 말고, 공고문에 명시된 **정확한 날짜/기간**을 그대로 추출하세요
- 예시: "2025년 9월 9일", "2025년 10월 1일 ~ 2026년 12월 31일", "2025.09.30(화) 14:00까지" 등"""
        elif feature_key == 'support_scale':
            # 지원규모: 숫자/금액만 필요
            content_instruction = f"""실제 {feature_type} 값 - **구체적인 숫자/금액을 반드시 포함** (예: '연간 최대 20억원 이내', '7.35억원 이내')"""
            date_emphasis = """
**⚠️ 매우 중요 (지원규모):**
- content 필드에는 **구체적인 숫자/금액**을 반드시 포함하세요
- 요약하지 말고, 공고문에 명시된 **정확한 금액/규모**를 그대로 추출하세요
- 예시: "연간 최대 20억원 이내", "7.35억원 이내", "100억원" 등
- **날짜나 기간 정보는 포함하지 마세요**"""
        else:
            # 사업명, 공고기관 등: 순수하게 해당 값만 (날짜/기간/숫자 불필요)
            content_instruction = f"""실제 {feature_type} 값만 추출 (예: '2025년 공공AX 프로젝트 사업', '과학기술정보통신부')"""
            date_emphasis = """
**⚠️ 매우 중요:**
- content 필드에는 **{feature_type} 값만** 추출하세요
- **다른 정보(날짜, 기간, 금액 등)를 섞지 마세요**
- 요약하지 말고, 공고문에 명시된 **정확한 {feature_type} 값**만 그대로 추출하세요
- 예시:
  * 사업명: "2025년 공공AX 프로젝트 사업" (날짜나 기간 정보 포함 금지)
  * 공고기관: "과학기술정보통신부" (날짜나 기간 정보 포함 금지)"""
        
        system_prompt = f"""당신은 정부 R&D 공고문을 분석하는 전문가입니다.
공고문의 첫 10페이지 (또는 그 이하)에서 '{feature_type}'의 **실제 값**을 추출해야 합니다.

⚠️ 매우 중요:
- "{feature_type}" 작성 방법이나 가이드가 **절대 아닙니다**
- 공고문에 **실제로 명시된 구체적인 값**을 찾으세요
- 제목, 헤더, 상단 부분을 우선 확인하세요

[분석 대상]
- Feature: {feature_type}
- 설명: {feature_description}

JSON 형식으로 반환:
{{
  "found": true/false,
  "title": "추출된 실제 {feature_type} 값",
  "content": "{content_instruction}",
  "full_content": "해당 값이 나타난 전체 문맥",
  "key_points": ["추출된 값의 특징이나 중요 사항"],
  "writing_strategy": {{
    "overview": "이 값의 의미 및 사업계획서 작성 시 활용 방법",
    "writing_tips": ["이 값을 사업계획서에 어떻게 반영할지 팁"],
    "common_mistakes": ["자주 발생하는 실수"],
    "example_phrases": ["사업계획서에서 사용할 수 있는 예시 문구"]
  }}
}}

{date_emphasis}

**실제 값을 찾을 수 없으면 found를 false로 반환하세요.**"""

        # 사용자 프롬프트: Feature 타입에 따라 조건부
        if requires_date:
            user_examples = f"""
  * {feature_type}: "2025년 9월 9일" 또는 "2025.09.09" (요약하지 말고 정확한 날짜)
  * 또는 "2025년 10월 1일 ~ 2026년 12월 31일" (기간인 경우 시작일과 종료일 모두 포함)
  * 또는 "2025.09.30(화) 14:00까지" (시간까지 포함된 경우)"""
            user_emphasis = "content 필드에는 구체적인 날짜/기간을 반드시 포함하세요."
        elif feature_key == 'support_scale':
            user_examples = f"""
  * {feature_type}: "연간 최대 20억원 이내" 또는 "7.35억원 이내" (정확한 숫자/금액)
  * **날짜나 기간 정보는 포함하지 마세요**"""
            user_emphasis = "content 필드에는 구체적인 숫자/금액만 포함하세요. 날짜/기간은 포함하지 마세요."
        else:
            user_examples = f"""
  * {feature_type}: "{feature_type} 값만" (예: 사업명이면 "2025년 공공AX 프로젝트 사업"만, 공고기관이면 "과학기술정보통신부"만)
  * **다른 정보(날짜, 기간, 금액 등)를 섞지 마세요**"""
            user_emphasis = f"content 필드에는 {feature_type} 값만 추출하세요. 다른 정보를 섞지 마세요."
        
        user_prompt = f"""첨부된 이미지는 '{file_name}' 파일의 첫 {len(images)}페이지 (최대 10페이지)입니다.

위 페이지에서 '{feature_type}'의 **실제 값**을 찾아서 추출하세요.

⚠️ 매우 중요:
- 제목, 헤더, 상단 부분을 주의 깊게 확인하세요
- 작성 방법/가이드가 아니라, 공고문에 실제로 적혀있는 값을 찾으세요
- 예를 들어:{user_examples}

JSON 형식으로 반환해주세요. {user_emphasis}"""

        messages_content = [{"type": "text", "text": user_prompt}]
        messages_content.extend(image_contents)

        # Vision API 호출
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": messages_content}
            ],
            response_format={"type": "json_object"},
            temperature=0  # 일관성 있는 결과
        )

        if not response.choices or not response.choices[0].message.content:
            print(f"    ⚠️  Vision API 응답 없음")
            return None

        result = json.loads(response.choices[0].message.content)

        if result.get("found"):
            print(f"    ✅ Vision API 추출 성공: {result.get('content', '')[:50]}...")
        else:
            print(f"    ⚠️  Vision API: 값 없음")

        return result

    except Exception as e:
        print(f"    ⚠️  Vision API 실패: {e}")
        return None

