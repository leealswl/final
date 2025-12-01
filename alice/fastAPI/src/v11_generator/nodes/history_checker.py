from ..state_types import ProposalGenerationState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

def history_checker(state: ProposalGenerationState) -> ProposalGenerationState:
    print('history_checker 실행')

   #  HISTORY_PROMPT = """

   #      [목차 데이터 (JSON List)]
   #      {toc_structure}

   #      [현재 작업 중인 목차 (Current State)]
   #      {target_chapter}

   #      [이미 작성 완료된 목차 리스트]
   #      {accumulated_data}

   #      당신은 '사업계획서 자동 생성 에이전트'의 두뇌로서, 다음 단계에 작성할 목차를 결정하는 **논리 판단 모듈**입니다.
   #      당신의 목표는 **작업의 연속성을 유지**하면서, 순차적으로 **'최하위 목차(Leaf Node)'**를 하나씩 선택하는 것입니다.

   #      아래 우선순위 규칙을 순차적으로 적용하여 단 하나의 목차를 선택하십시오.

   #      ────────────────────────────────
   #      [목차 선택 우선순위 규칙]

   #      1. **작업 연속성 유지 규칙 (최우선 순위)**
   #         - 만약 **[현재 작업 중인 목차]** 값이 존재하고,
   #         - 그 목차가 **[이미 작성 완료된 목차 리스트]에 포함되어 있지 않다면**,
   #         - 다른 조건을 따지지 말고 **무조건 [현재 작업 중인 목차]를 그대로 다시 선택**하십시오.
   #         - (이유: 아직 해당 목차의 작성이 완료되지 않았으므로, 작업을 계속 이어서 해야 함)

   #      2. **상위 목차(Container) 자동 건너뛰기**
   #         - 규칙 1에 해당하지 않아 새로운 목차를 선택해야 할 경우,
   #         - 목차 번호가 다른 번호의 접두사(Prefix)로 쓰이는 **'상위 목차'는 절대 선택하지 마십시오.**
   #         - 반드시 더 이상 쪼개지지 않는 **'최하위 목차(Leaf Node)'** 단위로만 선택해야 합니다.

   #      3. **논리적 순차 진행 (Next Step)**
   #         - 규칙 1(연속성 유지)이 적용되지 않는 경우(즉, 현재 목차가 비어있거나 작성이 완료된 경우),
   #         - 전체 목차 구조상 **[이미 작성 완료된 목차 리스트]에 없는** 가장 **앞선 순서의 최하위 목차**를 선택하십시오.
   #         - (예: 1.1이 완료되었으면 1.2를 선택)

   #      ────────────────────────────────
   #      [Thinking Process (내부 판단 예시)]

   #      Case A: 현재 작업 중인 목차가 "1.1 사업 배경"인데, 아직 완료 목록에 없음.
   #      - 판단: 아직 쓰는 중이다.
   #      - 결정: **"1.1 사업 배경"** 유지.

   #      Case B: 현재 작업 중인 목차가 "1.1 사업 배경"이고, 완료 목록에 "1.1 사업 배경"이 있음.
   #      - 판단: 1.1은 다 썼다. 다음 안 쓴 걸 찾자.
   #      - 구조 확인: 1.2가 있고 안 썼음.
   #      - 결정: **"1.2 사업 목표"** 선택.

   #      Case C: 현재 작업 중인 목차가 없고(null/empty), 1번(개요)은 상위 목차임.
   #      - 판단: 처음 시작하거나 리셋됨. 1번은 상위니까 건너뜀.
   #      - 결정: 1번 하위의 첫 번째인 **"1.1 사업 배경"** 선택.

   #      ────────────────────────────────
   #      [최종 출력 형식]

   #      <선택된 목차명>

   #      (주의: 번호, 설명 없이 오직 목차의 Title 텍스트만 출력할 것)
   #      ────────────────────────────────

   #      """
    HISTORY_PROMPT = """
      # Role
      당신은 사업계획서 목차를 **순서대로 빠짐없이** 실행하는 'Strict Sequential Iterator'입니다.
      당신의 임무는 [전체 목차 구조]를 분석하여, 작성해야 할 **가장 첫 번째 '최하위 목차(Leaf Node)'**를 찾아내는 것입니다.

      # Input Data
      1. [전체 목차 구조]: {toc_structure}
         (주의: '1.', '1.1', '2.' 등의 계층 번호가 포함됨)
      2. [현재 작업 중인 목차]: "{target_chapter}"
         (주의: 번호 없음)
      3. [완료된 목차 리스트]: {accumulated_data}
         (주의: 번호 없음)

      # Definition: [Leaf Node]란 무엇인가?
      - **상위 목차(Parent)**: 하위 목차를 포함하고 있는 껍데기입니다. (예: '1. 사업 개요' 밑에 '1.1 ...'이 있다면 '1. 사업 개요'는 상위 목차임)
      - **최하위 목차(Leaf Node)**: 더 이상 쪼개지지 않는 구체적인 작성 단위입니다. (예: '1.1 사업 배경')
      - **규칙**: 당신은 오직 **Leaf Node**만 선택할 수 있습니다. **상위 목차는 절대 선택하지 마십시오.**

      # Decision Algorithm (Step-by-Step)

      **Step 1. 현재 작업 확인 (Resume Check)**
      - [현재 작업 중인 목차]가 비어있지 않고,
      - [완료된 목차 리스트]에 그 텍스트가 **없다면**,
      - -> **무조건 [현재 작업 중인 목차]를 다시 출력**하고 종료하십시오. (작성 중인 작업 유지)

      **Step 2. 순차 탐색 (Sequential Scan)**
      - [전체 목차 구조]를 **맨 위에서부터 아래로 순서대로** 하나씩 검사하며 아래 로직을 적용합니다.

         1. **Is Parent? (상위 목차 여부 확인)**
            - 현재 검사 중인 항목이 하위 목차를 가지고 있다면(예: '1. 개요' 다음에 '1.1'이 온다면),
            - 이 항목은 **작성 대상이 아닙니다.** -> **SKIP(건너뛰기)** 하고 다음 항목으로 넘어가십시오.

         2. **Is Completed? (완료 여부 확인)**
            - 현재 항목이 **Leaf Node**라면, 항목의 번호를 제거한 텍스트를 추출합니다.
            - 이 텍스트가 [완료된 목차 리스트]에 포함되어 있는지 확인합니다.
            - 포함되어 있다면 -> **SKIP(이미 완료됨)**.

         3. **Select (선택)**
            - 위 1, 2번 조건에 걸리지 않은(상위 목차도 아니고, 완료되지도 않은) **첫 번째 항목**을 발견하면,
            - **즉시 탐색을 멈추고 그 항목을 선택**하십시오.

      **Step 3. 건너뛰기 금지 (Strict Rule)**
      - 예: 1.3이 완료되었고 1.4와 1.5가 남았다면, **반드시 1.4를 선택**해야 합니다. 1.5로 점프하지 마십시오.

      # Output Format
      - 선택된 목차의 **순수 텍스트(번호 제외)**만 출력하십시오.
      - 예: "사업 배경 및 목표"
      """

    toc_structure = state.get("draft_toc_structure", [])
    # toc_structure = state['draft_toc_structure']
   #  print('toc_structure: ', toc_structure)
   #  print(1)
    user_prompt = state.get('user_prompt', "").strip()
    accumulated_data = state.get('accumulated_data', [])

    print('accumulated_data: ', accumulated_data)

    target_chapter = state.get('target_chapter')

    print('target_chapter: ', target_chapter)

    llm = ChatOpenAI( model="gpt-4o")

    prompt = PromptTemplate.from_template(HISTORY_PROMPT)
    chain = prompt | llm | StrOutputParser()
    
    # chain.invoke()의 결과는 이제 순수한 파싱된 스트링입니다.
    result = chain.invoke({
        'toc_structure': toc_structure,
        'target_chapter': target_chapter,
        'accumulated_data': accumulated_data
    })
    
    print('----------------')
    print('선택된 목차: ', result)
    print('-----------------')

    # 만약 accumulated_data가 문자열이면 리스트로 변환
    # if isinstance(accumulated_data, str):
    #     accumulated_data = [accumulated_data]

    # accumulated_data.append(result)

    # print('accumulated_data: ', accumulated_data)

    return{ 'target_chapter': result,
           "accumulated_data": accumulated_data}
